import pandas as pd
import numpy as np
import geopandas as gpd
from libpysal.weights import KNN
from esda import Moran
from sklearn.metrics import r2_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
import json
import os
from sqlalchemy import create_engine, text
from datetime import datetime


# ---------- 1. RENT PRICE + SPATIAL AUTOCORRELATION ----------

def compute_spatial_patterns(apartments_for_rent):
    gdf = gpd.GeoDataFrame(
        apartments_for_rent,
        geometry=gpd.points_from_xy(apartments_for_rent.longitude, apartments_for_rent.latitude),
        crs="EPSG:4326"
    )
    w = KNN.from_dataframe(gdf, k=8)
    w.transform = "R"

    moran = Moran(gdf["rent_per_person"], w)
    mean_rent = gdf["rent_per_person"].mean()

    rent_by_neigh = None
    if "neighborhood" in gdf.columns:
        rent_by_neigh = (
            gdf.groupby("neighborhood")["rent_per_person"]
            .mean()
            .sort_values(ascending=False)
        )

    return {
        "global_moran": {"I": moran.I, "p_value": moran.p_sim},
        "mean_rent": mean_rent,
        "rent_by_neighborhood": rent_by_neigh,
    }


# ---------- 2. LANDLORD BEHAVIOR ----------

def analyze_landlords(gdf):
    if "owner_name" not in gdf.columns or "differenceinfairvalue" not in gdf.columns:
        return None

    gdf_copy = gdf.copy()
    gdf_copy["owner_name_str"] = gdf_copy["owner_name"].astype(str)
    
    gdf_copy = gdf_copy.dropna(subset=["owner_name_str"])
    gdf_copy = gdf_copy[gdf_copy["owner_name_str"] != "nan"]
    gdf_copy = gdf_copy[gdf_copy["owner_name_str"] != ""]
    gdf_copy = gdf_copy[gdf_copy["owner_name_str"] != "{}"]

    if len(gdf_copy) == 0:
        return None

    multi_landlords = gdf_copy.groupby("owner_name_str").filter(lambda x: len(x) >= 3)
    
    if len(multi_landlords) == 0:
        return None
        
    top_landlords = (
        multi_landlords.groupby("owner_name_str")["differenceinfairvalue"]
        .mean()
        .sort_values(ascending=False)
        .head(5)
    )

    return top_landlords


# ---------- 3. OVERPRICING STATISTICS ----------

def analyze_overpricing(gdf):
    overpriced_pct = (gdf["differenceinfairvalue"] > 0).mean() * 100

    avg_overpricing_by_neigh = None
    if "neighborhood" in gdf.columns:
        avg_overpricing_by_neigh = (
            gdf.groupby("neighborhood")["differenceinfairvalue"].mean()
        )

    return {
        "percent_overpriced": overpriced_pct,
        "avg_overpricing_by_neighborhood": avg_overpricing_by_neigh,
    }


# ---------- 4. MODEL PERFORMANCE ----------

def summarize_model_performance(results_df, best_model_name):
    results_df = results_df.set_index(results_df.index.astype(str))
    top_model_row = results_df.loc[str(best_model_name)]

    return {
        "all_model_metrics": results_df[["R2", "RMSE", "MAPE"]],
        "best_model": str(best_model_name),
        "best_model_metrics": {
            "R2": top_model_row["R2"],
            "RMSE": top_model_row["RMSE"],
            "MAPE": top_model_row["MAPE"],
        },
    }


# ---------- 5. FEATURE IMPORTANCE ----------

def compute_feature_importance(best_model_name, X_spatial, y):
    if "RandomForest" not in best_model_name:
        return None

    rf = RandomForestRegressor(n_estimators=200, max_depth=12, random_state=42)
    rf.fit(X_spatial, y)
    perm = permutation_importance(rf, X_spatial, y, n_repeats=20, random_state=42)
    feature_importance = pd.DataFrame({
        "feature": X_spatial.columns.astype(str),
        "importance": perm.importances_mean,
    }).sort_values("importance", ascending=False)

    spatial_features = feature_importance[
        feature_importance["feature"].astype(str).str.startswith("W_")
    ]

    return {
        "all_features": feature_importance,
        "spatial_features": spatial_features.head(5)
    }


# ---------- 6. SPATIAL RESIDUALS + LOCAL MODEL CHECK ----------

def spatial_residual_analysis(gdf):
    w = KNN.from_dataframe(gdf, k=8)
    residuals = gdf["differenceinfairvalue"]
    moran_res = Moran(residuals, w)

    r2_by_nbhd = None
    if "neighborhood" in gdf.columns:
        r2_by_nbhd = (
            gdf.groupby("neighborhood")
            .apply(lambda x: r2_score(x["rent_per_person"], x["predictedrent"])
                   if len(x) > 3 else np.nan)
            .dropna()
        )

    return {
        "residual_moran": {"I": moran_res.I, "p_value": moran_res.p_sim},
        "r2_by_neighborhood": r2_by_nbhd,
    }


# ---------- MAIN WRAPPER ----------

def analyze_market_and_model(apartments_for_rent, results_df, X, X_spatial, y, best_model_name):
    """
    Returns dashboard-ready analysis dict with all components.
    """
    gdf = gpd.GeoDataFrame(
        apartments_for_rent,
        geometry=gpd.points_from_xy(apartments_for_rent.longitude, apartments_for_rent.latitude),
        crs="EPSG:4326"
    )

    analysis = {
        "spatial_patterns": compute_spatial_patterns(apartments_for_rent),
        "landlord_behavior": analyze_landlords(gdf),
        "overpricing": analyze_overpricing(gdf),
        "model_performance": summarize_model_performance(results_df, best_model_name),
        "feature_importance": compute_feature_importance(best_model_name, X_spatial, y),
        "spatial_residuals": spatial_residual_analysis(gdf),
    }

    return analysis


# ---------- DATABASE INSERTION ----------

def serialize_metrics(analysis_dict):
    """
    Convert numpy types and pandas objects to JSON-serializable format
    """
    def convert_to_serializable(obj):
        try:
            if obj is None:
                return None
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, pd.Series):
                return {str(k): convert_to_serializable(v) for k, v in obj.to_dict().items()}
            elif isinstance(obj, pd.DataFrame):
                return obj.to_dict('records')
            elif hasattr(obj, 'tolist'): 
                return obj.tolist()
            elif isinstance(obj, dict):
                return {str(k): convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(item) for item in obj]
            elif isinstance(obj, (str, int, float, bool)):
                return obj
            else:
                return str(obj)
        except Exception as e:
            print(f"Warning: Could not serialize object {type(obj)}: {e}")
            return str(obj)
    
    return convert_to_serializable(analysis_dict)


def insert_pipeline_metrics(analysis_dict):
    """
    Insert pipeline metrics into the rental_model_runs table
    """
    try:
        DB_URI = os.getenv("DB_URI")
        if not DB_URI:
            print("⚠️ DB_URI not found, skipping metrics insertion")
            return
        
        engine = create_engine(DB_URI)
        
        serialized_metrics = serialize_metrics(analysis_dict)
        
        run_record = {
            'run_timestamp': datetime.now(),
            'spatial_patterns': json.dumps(serialized_metrics.get('spatial_patterns', {})),
            'landlord_behavior': json.dumps(serialized_metrics.get('landlord_behavior', {})),
            'overpricing': json.dumps(serialized_metrics.get('overpricing', {})),
            'model_performance': json.dumps(serialized_metrics.get('model_performance', {})),
            'feature_importance': json.dumps(serialized_metrics.get('feature_importance', {})),
            'spatial_residuals': json.dumps(serialized_metrics.get('spatial_residuals', {}))
        }
        
        with engine.begin() as conn:
            insert_query = text("""
                INSERT INTO rental_model_runs 
                (run_timestamp, spatial_patterns, landlord_behavior, overpricing, 
                 model_performance, feature_importance, spatial_residuals)
                VALUES (:run_timestamp, :spatial_patterns, :landlord_behavior, :overpricing,
                        :model_performance, :feature_importance, :spatial_residuals)
            """)
            
            conn.execute(insert_query, run_record)
            
        print("✅ Pipeline metrics inserted into rental_model_runs table")
        
    except Exception as e:
        print(f"❌ Error inserting pipeline metrics: {e}")
        import traceback
        traceback.print_exc()