"""Production rent prediction: one XGBoost per held-out-property fold.

The spatial OOF challenger is in ml/archive/spatial_oof.py. Older spatial lag,
two-stage XGBoost, and alternative regression models are in
ml/archive/model_training_legacy.py.

We generate honest out-of-fold (OOF) estimates for existing properties. All
listings from the same PropertyId stay together, preventing own-property rents
from becoming training labels for their own market benchmarks.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold


# Notebook model: separate baseline, bedrooms/bathrooms, and advertised amenities.
# Keep names explicit so each family can be toggled without retraining on
# different undisclosed inputs.
UNIT_AMENITIES = (
    "has_ac", "has_heating", "has_dishwasher", "is_furnished",
    "has_in_unit_laundry", "has_microwave", "has_oven",
    "has_refrigerator", "has_stainless_appliances", "has_garbage_disposal",
    "has_hardwood_floors", "has_granite_countertops",
    "has_quartz_countertops", "has_private_bathroom", "has_walk_in_closet",
    "has_fireplace", "has_ceiling_fan", "has_keyless_entry",
    "has_private_entrance", "has_private_balcony", "has_porch",
    "has_patio", "has_high_ceilings",
)
BUILDING_AMENITIES = (
    "has_fitness_center", "has_pool", "has_elevator", "has_study_room",
    "has_resident_lounge", "has_rooftop_terrace", "has_sauna",
    "has_courtyard", "has_yard", "has_grill", "has_bike_storage",
    "has_ev_charging", "has_security_cameras", "has_controlled_access",
    "has_package_room", "has_onsite_management", "has_onsite_maintenance",
    "has_emergency_maintenance", "has_shared_laundry", "has_laundry",
    "has_storage", "parking_available", "has_private_shuttle",
    "ada_accessible_advertised",
)
UTILITY_AMENITIES = (
    "heat_included_verified", "electricity_included_verified",
    "water_included_verified", "internet_included_verified",
    "trash_included_verified", "electricity_advertised",
    "water_advertised", "trash_advertised", "gas_advertised",
    "hot_water_advertised", "internet_available", "internet_ready",
    "cable_ready", "snow_removal_advertised", "lawn_care_included",
    "utilities_included",
)
LEASING_AMENITIES = (
    "per_person_leasing", "roommate_matching_available",
    "academic_term_lease", "short_term_lease_available",
    "furnishing_option_available", "pets_negotiable", "no_pets_allowed",
    "cats_allowed_advertised", "dogs_allowed_advertised",
)

USE_BASELINE_FEATURES = True
USE_SQFT = True
USE_SEPARATE_BEDS_BATHS = True
USE_UNIT_AMENITIES = True
USE_BUILDING_AMENITIES = True
USE_UTILITY_AMENITIES = True
USE_LEASING_AMENITIES = True
EXCLUDE_FEATURES = ()
INCLUDE_FEATURES = ()

BASELINE_FEATURES = (
    "pets", "combined_bedrooms_bathrooms", "walk_time_urishall",
    "transit_score", "valid_certificate_of_compliance",
    "yr_built_encoded", "electricity_included", "heat_included",
    "water_included", "internet_included", "laundry_facilities",
    "air_conditioning", "furnished", "food_nearest_dist",
    "food_count_200m", "attractions_nearest_dist",
    "attractions_count_200m", "shopping_nearest_dist",
    "shopping_count_200m", "grocery_nearest_dist",
    "grocery_count_200m", "latitude", "longitude",
    "x_meters", "y_meters", "submarket", "assessment_per_sqft",
)
# Fresh-ingest dataframe uses title-case names in some legacy transforms;
# DB-only rerun has lowercase SQL columns as well.
BASELINE_ALIASES = {
    "pets": "Pets",
    "yr_built_encoded": "YR_BUILT_ENCODED",
    "electricity_included": "Electricity Included",
    "heat_included": "Heat Included",
    "water_included": "Water Included",
    "internet_included": "Internet Included",
    "laundry_facilities": "Laundry Facilities",
    "air_conditioning": "Air Conditioning",
    "furnished": "Furnished",
}


def define_X_Y_variables(apartments_for_rent):
    """Production features matching IthacaInsightsNewDev.ipynb's enabled toggles.

    Resolve legacy title-case aliases without changing canonical feature names;
    remove all-missing and constant predictors as in the notebook. Target and
    identifiers never enter the feature matrix.
    """
    frame = apartments_for_rent
    selected = []
    if USE_BASELINE_FEATURES:
        selected.extend(BASELINE_FEATURES)
    if USE_SQFT:
        selected.append("unit_sqft")
    if USE_SEPARATE_BEDS_BATHS:
        selected.extend(("physical_bedrooms", "available_bedrooms", "available_bathrooms"))
    # Nullable: XGBoost routes unknown shared-facility status natively.
    selected.append("shared_facilities")
    if USE_UNIT_AMENITIES:
        selected.extend(UNIT_AMENITIES)
    if USE_BUILDING_AMENITIES:
        selected.extend(BUILDING_AMENITIES)
    if USE_UTILITY_AMENITIES:
        selected.extend(UTILITY_AMENITIES)
    if USE_LEASING_AMENITIES:
        selected.extend(LEASING_AMENITIES)
    selected.extend(("model_bedrooms", "shared_facilities"))
    selected.extend(INCLUDE_FEATURES)
    selected = [c for c in dict.fromkeys(selected) if c not in EXCLUDE_FEATURES]

    columns = {}
    for name in selected:
        source = name if name in frame.columns else BASELINE_ALIASES.get(name)
        if source is not None and source in frame.columns:
            columns[name] = pd.to_numeric(frame[source], errors="coerce")
        elif name not in BASELINE_FEATURES:
            raise ValueError(f"Missing required notebook predictor: {name}")
    X = pd.DataFrame(columns, index=frame.index).replace([np.inf, -np.inf], np.nan)
    # Match notebook preprocessing, without leaking any rent/target values.
    X = X.loc[:, X.notna().any()]
    X = X.loc[:, X.nunique(dropna=True) > 1]
    if X.empty:
        raise ValueError("No usable rent predictors present")
    print(f"📋 Production notebook rent predictors ({len(X.columns)}): {list(X.columns)}")
    return X, frame["rent_per_person"].copy()


def group_by_property_df(df):
    """All unit rows for a building must receive the same CV fold."""
    if "PropertyId" in df:
        return df["PropertyId"].astype(str)
    if "ListingId" in df:
        return df["ListingId"].astype(str).str.rsplit("-", n=1).str[0]
    raise ValueError("OOF requires PropertyId or ListingId for grouped folds")


def _model_features(train, test):
    """Numerical features for XGBoost; keep missing values as NaN.

    Never estimate imputation statistics globally before the fold split.
    """
    train = train.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    test = test.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    return train.astype(float), test.astype(float)


def _dollar_metrics(actual, predicted):
    """Errors are actual minus prediction, all measured in $/person/month."""
    errors = np.asarray(actual, dtype=float) - np.asarray(predicted, dtype=float)
    return {
        "r2": float(r2_score(actual, predicted)) if len(actual) >= 2 else float("nan"),
        "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
        "mae": float(mean_absolute_error(actual, predicted)),
        "bias": float(np.mean(errors)),
        "median_residual": float(np.median(errors)),
        "residual_std": float(np.std(errors, ddof=1)) if len(errors) > 1 else float("nan"),
        "p90_abs_error": float(np.percentile(np.abs(errors), 90)),
    }


def compute_fair_rent_oof(
    apartments_for_rent,
    y,
    x_cols,
    h3_reses=(6, 7),
    k_knn=10,
    n_splits=5,
    n_estimators=100,
    max_depth=6,
):
    """Predict each unit with a single XGBoost trained on OTHER properties.

    Parameters h3_reses and k_knn are accepted for compatibility only; target
    encoding, nearby target rents, and residual-lag models are deliberately
    disabled. See the archived experiments if those are revisited.

    y must contain LOG rents. Returns:
      (listings_with_oof_predictions, fold_metrics_df, overall_metrics_dict,
       feature_importance_df)

    All reported errors are in dollars after exp(log_pred), not log units.
    """
    frame = apartments_for_rent.copy().reset_index(drop=True)
    log_y = np.asarray(y, dtype=float).reshape(-1)
    if len(frame) != len(log_y):
        raise ValueError("Length mismatch between listings and log-rent target")
    if not np.isfinite(log_y).all():
        raise ValueError("OOF log-rent targets must be finite")

    groups = group_by_property_df(frame)
    n_props = int(groups.nunique())
    folds = min(n_splits, n_props)
    if folds < 2:
        raise ValueError(f"At least two distinct properties required, found {n_props}")

    # Explicitly use only requested available numerical predictors, and avoid
    # target-derived fields even if a caller accidentally includes them.
    forbidden = {
        "rent_per_person", "rentamount", "RentAmount", "actual_rent",
        "fair_rent", "predictedrent", "log_rent", "log_fair_rent",
        "pct_mispricing", "mispricing", "mispricing_pct",
        "rent_per_person_original", "total_rent_amount",
    }
    features = [
        col for col in dict.fromkeys(list(x_cols) + ["latitude", "longitude"])
        if col in frame.columns and col not in forbidden and
        not str(col).startswith(("knn_", "h3_")) and col != "spatial_cluster"
    ]
    if not features:
        raise ValueError("No model features available after excluding target columns")

    log_pred = np.full(len(frame), np.nan)
    fold_rows = []
    importance = []

    print(f"🏢 OOF XGBoost: {n_props} properties, {folds} folds, "
          f"{len(frame)} unit rows, {len(features)} predictors")

    splitter = GroupKFold(n_splits=folds)
    for fold_id, (train_pos, test_pos) in enumerate(
        splitter.split(frame, log_y, groups), start=1
    ):
        x_train, x_test = _model_features(
            frame.iloc[train_pos][features],
            frame.iloc[test_pos][features],
        )
        model = xgb.XGBRegressor(
            n_estimators=n_estimators, max_depth=max_depth,
            learning_rate=0.1, subsample=0.8, colsample_bytree=0.8,
            random_state=42, n_jobs=-1, missing=np.nan,
        )
        model.fit(x_train, log_y[train_pos])
        fold_log_pred = model.predict(x_test)
        log_pred[test_pos] = fold_log_pred

        actual = np.exp(log_y[test_pos])
        predicted = np.exp(fold_log_pred)
        row = {
            "fold": fold_id,
            "train_properties": int(groups.iloc[train_pos].nunique()),
            "test_properties": int(groups.iloc[test_pos].nunique()),
            "test_listings": int(len(test_pos)),
            **_dollar_metrics(actual, predicted),
        }
        fold_rows.append(row)
        print(
            f"  Fold {fold_id}/{folds}: {row['test_properties']} held-out properties "
            f"({row['test_listings']} listings) | R²={row['r2']:.3f} | "
            f"RMSE=${row['rmse']:,.0f} | MAE=${row['mae']:,.0f} | "
            f"bias(actual−pred)=${row['bias']:+,.0f} | "
            f"residual SD=${row['residual_std']:,.0f}"
        )

        # XGBoost gain measures predictive split improvement, not causality.
        gains = model.get_booster().get_score(importance_type="gain")
        score = pd.Series({name: float(gains.get(name, 0.0)) for name in features})
        if score.sum() > 0:
            score = score / score.sum()
        importance.append(score.rename(f"fold_{fold_id}"))

    if not np.isfinite(log_pred).all():
        raise ValueError("Missing or non-finite OOF predictions")
    actual_all = np.exp(log_y)
    predicted_all = np.exp(log_pred)
    overall = {
        "n_properties": n_props,
        "n_listings": len(frame),
        "n_folds": folds,
        **_dollar_metrics(actual_all, predicted_all),
    }
    print(
        f"📊 OVERALL OOF (pooled {len(frame)} listings): "
        f"R²={overall['r2']:.3f} | RMSE=${overall['rmse']:,.0f} | "
        f"MAE=${overall['mae']:,.0f} | bias(actual−pred)=${overall['bias']:+,.0f} | "
        f"p90 absolute error=${overall['p90_abs_error']:,.0f}"
    )
    print("ℹ️ Bias/residuals use actual minus predicted: positive = model underpredicts.")

    importance_df = (
        pd.concat(importance, axis=1)
        .mean(axis=1)
        .sort_values(ascending=False)
        .rename("mean_normalized_gain")
        .reset_index()
        .rename(columns={"index": "feature"})
    )
    print("⭐ Top overall features (mean normalized XGBoost gain across folds):")
    for _, rec in importance_df.head(15).iterrows():
        print(f"  {rec['feature']}: {rec['mean_normalized_gain']:.1%}")
    print("ℹ️ Feature gain is predictive importance, not a causal effect.")

    frame["log_rent"] = log_y
    frame["log_fair_rent"] = log_pred
    frame["actual_rent"] = actual_all
    frame["fair_rent"] = predicted_all
    frame["mispricing"] = actual_all - predicted_all
    frame["pct_mispricing"] = frame["mispricing"] / predicted_all
    frame["mispricing_pct"] = frame["mispricing"] / actual_all
    return frame, pd.DataFrame(fold_rows), overall, importance_df

