"""
Rerun fair-rent / CMA predictions from existing housing_listings rows.

Does NOT scrape or re-geocode. Rebuilds ML features that can be derived from
DB columns (amenity one-hots, bed/bath combo, year encoding), runs spatial CV
+ property-grouped OOF fair rent + CMA, then UPDATEs prediction columns only.
"""
from __future__ import annotations

import ast
import json
import os
import time
from decimal import Decimal

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, DBAPIError

import calculators.calculate_amenity_score as calculate_amenity_score
import core.pipeline_metrics as pipeline_metrics
import ml.comparative_market_analysis as comparative_market_analysis
import ml.data_preprocessing as data_preprocessing
import ml.model_training as model_training


PREDICTION_UPDATE_COLS = [
    "predictedrent",
    "predicted_rent_cma",
    "nearest_neighbor_listingids",
    "differenceinfairvalue",
]


def _engine():
    db_uri = os.getenv("DB_URI")
    if not db_uri:
        raise ValueError("DB_URI environment variable not set")
    return create_engine(
        db_uri,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=1,
        max_overflow=0,
        connect_args={
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
            "connect_timeout": 30,
        },
    )


def _existing_columns(conn) -> set[str]:
    rows = conn.execute(
        text(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'housing_listings'
            """
        )
    ).fetchall()
    return {r[0] for r in rows}


def fetch_listings_for_retrain() -> pd.DataFrame:
    """Load current listings from Postgres for ML retrain."""
    wanted = [
        "listingid",
        "listingaddress",
        "listingcity",
        "listingzip",
        "latitude",
        "longitude",
        "rentamount",
        "renttype",
        "rent_per_person",
        "num_people",
        "total_rent_amount",
        "bedrooms",
        "bathrooms",
        "available_bedrooms",
        "available_bathrooms",
        "pets",
        "amenities",
        "amenities_score",
        "transit_score",
        "valid_certificate_of_compliance",
        "year_built",
        "sale_price",
        "assessment_sqft",
        "neighborhood",
        "owner_name",
        "lengthavailable",
        "walk_time_urishall",
        "walk_time_agriculturequad",
        "walk_time_artsquad",
        "walk_time_engineeringquad",
        "bike_time_urishall",
        "bike_time_agriculturequad",
        "bike_time_artsquad",
        "bike_time_engineeringquad",
        "drive_time_urishall",
        "drive_time_agriculturequad",
        "drive_time_artsquad",
        "drive_time_engineeringquad",
        "nearest_stop_name",
        "walk_time_to_nearest_stop",
        "transit_time_to_ag_quad",
        "transit_time_to_arts_quad",
        "transit_time_to_eng_quad",
    ]

    engine = _engine()
    with engine.connect() as conn:
        present = _existing_columns(conn)
        cols = [c for c in wanted if c in present]
        if "listingid" not in cols:
            raise ValueError("housing_listings missing listingid")
        query = text(f"SELECT {', '.join(cols)} FROM housing_listings")
        df = pd.read_sql(query, conn)

    print(f"📊 Loaded {len(df)} listings from housing_listings ({len(cols)} columns)")
    return df


def _parse_amenities(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
        try:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, list):
                return parsed
        except (ValueError, SyntaxError):
            pass
    return []


def prepare_features_from_db(df: pd.DataFrame) -> pd.DataFrame:
    """Map DB columns → training frame used by define_X_Y / fair-rent OOF."""
    out = df.copy()

    # Identity / grouping
    out["ListingId"] = out["listingid"].astype(str)
    out["PropertyId"] = out["ListingId"].str.rsplit("-", n=1).str[0]

    # Title-case aliases expected by some helpers
    rename_map = {
        "bedrooms": "Bedrooms",
        "bathrooms": "Bathrooms",
        "pets": "Pets",
        "amenities": "Amenities",
        "lengthavailable": "LengthAvailable",
    }
    for src, dst in rename_map.items():
        if src in out.columns and dst not in out.columns:
            out[dst] = out[src]

    if "Amenities" in out.columns:
        out["Amenities"] = out["Amenities"].apply(_parse_amenities)
        out = calculate_amenity_score.calculate_amenity_score(out)

    # Bed/bath features
    if "available_bedrooms" not in out.columns and "Bedrooms" in out.columns:
        out["available_bedrooms"] = out["Bedrooms"]
    if "available_bathrooms" not in out.columns and "Bathrooms" in out.columns:
        out["available_bathrooms"] = out["Bathrooms"]
    if "Bedrooms" in out.columns:
        out = data_preprocessing.calc_adjusted_bed_bath_values(out)

    out = data_preprocessing.add_property_features(out)

    # CMA lat/lng aliases
    if "GmapLatitude" not in out.columns and "latitude" in out.columns:
        out["GmapLatitude"] = out["latitude"]
    if "GmapLongitude" not in out.columns and "longitude" in out.columns:
        out["GmapLongitude"] = out["longitude"]

    # Pets → numeric 0/1 when possible
    if "Pets" in out.columns:
        pets = out["Pets"]
        if pets.dtype == object:
            out["Pets"] = pets.map(
                lambda x: 1
                if str(x).strip().lower() in {"1", "true", "yes", "y"}
                else 0
                if str(x).strip().lower() in {"0", "false", "no", "n", "nan", ""}
                else pd.to_numeric(x, errors="coerce")
            )
        out["Pets"] = pd.to_numeric(out["Pets"], errors="coerce").fillna(0)

    # Keep rows usable for supervised rent prediction
    before = len(out)
    out["rent_per_person"] = pd.to_numeric(out.get("rent_per_person"), errors="coerce")
    out["latitude"] = pd.to_numeric(out.get("latitude"), errors="coerce")
    out["longitude"] = pd.to_numeric(out.get("longitude"), errors="coerce")
    out = out[
        out["rent_per_person"].notna()
        & (out["rent_per_person"] > 0)
        & out["latitude"].notna()
        & out["longitude"].notna()
    ].copy()
    print(
        f"🧹 Trainable rows after rent/coord filter: {len(out)}/{before} "
        f"({out['PropertyId'].nunique()} properties)"
    )
    if out.empty:
        raise ValueError("No listings with rent_per_person + coordinates available to retrain")

    return out.reset_index(drop=True)


def run_ml_and_cma(apartments_for_rent: pd.DataFrame):
    """Compare baseline versus spatial XGBoost using identical property OOF folds.

    Both methods predict the same listings. Keep BASELINE predictions as the
    stored website values until the spatial challenger is explicitly selected.
    """
    apartments_for_rent = apartments_for_rent.reset_index(drop=True).copy()
    X, dollars = model_training.define_X_Y_variables(apartments_for_rent)
    # Missing values are handled natively by XGBoost, within each training fold.
    X = X.apply(pd.to_numeric, errors="coerce").replace(
        [np.inf, -np.inf], np.nan
    )
    for col in X.columns:
        apartments_for_rent[col] = X[col].to_numpy()
    y = np.log(pd.to_numeric(dollars, errors="coerce").to_numpy(dtype=float))

    print("🏢 Running baseline XGBoost OOF...")
    baseline_df, base_folds, base_overall, base_features = (
        model_training.compute_fair_rent_oof(
            apartments_for_rent=apartments_for_rent, y=y,
            x_cols=list(X.columns), n_splits=5,
            n_estimators=100, max_depth=6,
        )
    )
    print("🗺️ Running spatial XGBoost OOF (H3 + other-property KNN; no coordinates)...")
    spatial_df, spatial_folds, spatial_overall, spatial_features = (
        model_training.compute_fair_rent_oof_spatial(
            apartments_for_rent=apartments_for_rent, y=y,
            x_cols=list(X.columns), h3_reses=(6, 7), k_knn=10,
            n_splits=5, n_estimators=100, max_depth=6,
        )
    )

    print("\\n📊 Fold-by-fold comparison ($/person/month):")
    comparison = base_folds[["fold", "test_properties", "test_listings",
                            "r2", "rmse", "mae", "bias"]].merge(
        spatial_folds[["fold", "r2", "rmse", "mae", "bias"]],
        on="fold", suffixes=("_baseline", "_spatial"),
        validate="one_to_one",
    )
    print(comparison.to_string(index=False, float_format=lambda v: f"{v:,.2f}"))
    rows = []
    for name, metrics in (("Baseline", base_overall), ("Spatial", spatial_overall)):
        rows.append({"model": name, **metrics})
    overview = pd.DataFrame(rows).set_index("model")
    print("\\n🏆 Pooled grouped OOF performance:")
    print(overview[["r2", "rmse", "mae", "bias", "p90_abs_error"]].to_string(
        float_format=lambda v: f"{v:,.2f}"
    ))
    print(f"Δ RMSE (spatial - baseline): "
          f"${spatial_overall['rmse'] - base_overall['rmse']:+,.2f}")
    print(f"Δ MAE (spatial - baseline): "
          f"${spatial_overall['mae'] - base_overall['mae']:+,.2f}")
    print("\\n⭐ Baseline top features:")
    print(base_features.head(12).to_string(index=False))
    print("\\n⭐ Spatial top features:")
    print(spatial_features.head(12).to_string(index=False))
    print("ℹ️ Feature gains measure predictive contribution, not causal effects.")
    print("ℹ️ Baseline OOF predictions remain the DB output; spatial runs as challenger.")

    apartments_for_rent = baseline_df
    apartments_for_rent["predictedrent"] = apartments_for_rent["fair_rent"]
    apartments_for_rent["PredictedRent"] = apartments_for_rent["fair_rent"]
    apartments_for_rent["differenceinfairvalue"] = (
        apartments_for_rent["rent_per_person"] - apartments_for_rent["predictedrent"]
    )
    apartments_for_rent["DifferenceinFairValue"] = apartments_for_rent["differenceinfairvalue"]

    print("📈 Running CMA for baseline predictions...")
    X_cma = comparative_market_analysis.define_X_for_cma(apartments_for_rent)
    apartments_for_rent = comparative_market_analysis.perform_cma(
        X_cma, apartments_for_rent
    )

    results_df = pd.DataFrame(
        {
            "R2": [base_overall["r2"], spatial_overall["r2"]],
            "RMSE": [base_overall["rmse"], spatial_overall["rmse"]],
            "MAE": [base_overall["mae"], spatial_overall["mae"]],
            "MAPE": [None, None],
            "flagged": [False, False],
        },
        index=["Baseline Property OOF XGBoost", "Spatial Property OOF XGBoost"],
    )
    results = {
        "baseline": {"folds": base_folds, "overall": base_overall, "features": base_features},
        "spatial": {"folds": spatial_folds, "overall": spatial_overall, "features": spatial_features},
    }
    return apartments_for_rent, results_df, X, X, y, results

def _sanitize(v):
    if v is None:
        return None
    if isinstance(v, float) and pd.isna(v):
        return None
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (np.floating, np.integer)):
        return v.item()
    if isinstance(v, (list, dict)):
        return json.dumps(v)
    return v


def update_predictions_in_db(df: pd.DataFrame, batch_size: int = 100) -> int:
    """UPDATE prediction columns for ListingIds present in df."""
    engine = _engine()

    records = []
    for _, row in df.iterrows():
        neighbors = row.get("nearest_neighbor_listingIds", row.get("nearest_neighbor_listingids"))
        if isinstance(neighbors, (list, dict)):
            neighbors = json.dumps(neighbors)
        elif neighbors is not None and not isinstance(neighbors, str):
            neighbors = json.dumps(neighbors)

        records.append(
            {
                "listingid": str(row["ListingId"]),
                "predictedrent": _sanitize(row.get("predictedrent")),
                "predicted_rent_cma": _sanitize(row.get("predicted_rent_cma")),
                "nearest_neighbor_listingids": neighbors,
                "differenceinfairvalue": _sanitize(row.get("differenceinfairvalue")),
            }
        )

    update_sql = text(
        """
        UPDATE housing_listings
        SET predictedrent = :predictedrent,
            predicted_rent_cma = :predicted_rent_cma,
            nearest_neighbor_listingids = :nearest_neighbor_listingids,
            differenceinfairvalue = :differenceinfairvalue
        WHERE listingid = :listingid
        """
    )

    updated = 0
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        for attempt in range(1, 4):
            try:
                with engine.begin() as conn:
                    conn.execute(update_sql, batch)
                updated += len(batch)
                break
            except (OperationalError, DBAPIError) as e:
                if attempt == 3:
                    raise
                print(f"⚠️ Update batch failed (attempt {attempt}): {e}; retrying...")
                try:
                    engine.dispose()
                except Exception:
                    pass
                time.sleep(2 * attempt)
        if (i // batch_size) % 5 == 0 or updated == len(records):
            print(f"💾 Updated predictions {updated}/{len(records)}")

    print(f"✅ Updated prediction columns for {updated} listings")
    return updated


def rerun_rent_prediction_pipeline():
    """
    End-to-end: DB → feature prep → ML/CMA → UPDATE predictions (+ metrics).
    """
    print("🚀 Starting rent-prediction re-run from database (no scrape)")

    raw = fetch_listings_for_retrain()
    apartments = prepare_features_from_db(raw)

    apartments, results_df, X, X_spatial, y_clean, evaluations = run_ml_and_cma(apartments)

    update_predictions_in_db(apartments)

    print("📊 Generating pipeline metrics...")
    try:
        metrics = pipeline_metrics.analyze_market_and_model(
            apartments,
            results_df,
            X,
            X_spatial,
            y_clean,
            "Baseline Property OOF XGBoost",
            oof_feature_importance=evaluations["baseline"]["features"],
            oof_fold_metrics=evaluations["baseline"]["folds"],
            oof_overall_metrics=evaluations["baseline"]["overall"],
        )
        metrics["model_performance"]["spatial_challenger"] = {
            "fold_metrics": evaluations["spatial"]["folds"].to_dict("records"),
            "overall_oof": evaluations["spatial"]["overall"],
        }
        metrics["model_performance"]["spatial_feature_importance"] = (
            evaluations["spatial"]["features"].set_index("feature")["mean_normalized_gain"].to_dict()
        )
        pipeline_metrics.insert_pipeline_metrics(metrics)
    except Exception as e:
        print(f"⚠️ Error generating pipeline metrics: {e}")
        import traceback

        traceback.print_exc()

    base = evaluations["baseline"]["overall"]
    spatial = evaluations["spatial"]["overall"]
    print(f"✅ Rent prediction re-run complete: baseline RMSE=${base['rmse']:,.2f}, "
          f"spatial RMSE=${spatial['rmse']:,.2f} ({len(apartments)} listings)")
    return {
        "n_listings": int(len(apartments)),
        "rmse": float(base["rmse"]),
        "r2": float(base["r2"]),
        "baseline": dict(base),
        "spatial": dict(spatial),
    }
