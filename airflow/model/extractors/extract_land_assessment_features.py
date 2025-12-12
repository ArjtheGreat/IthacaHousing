import pandas as pd
import numpy as np
import os
from pathlib import Path
import ast
import geopandas as gpd
from shapely.geometry import Polygon
from sklearn.impute import KNNImputer
from sklearn.cluster import KMeans
from sklearn.cluster import KMeans

def get_tompkins_county_data_path():
    """Get the path to TompkinsCountyData.csv, trying multiple locations"""
    BASE_DIR = "/opt/airflow/model"
    if not os.path.exists(BASE_DIR):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    possible_paths = [
        os.path.join(BASE_DIR, "data", "TompkinsCountyData.csv"),
        "/opt/airflow/model/data/TompkinsCountyData.csv",
        "/opt/airflow/model/TompkinsCountyData.csv",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "TompkinsCountyData.csv"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "TompkinsCountyData.csv"),
        "./data/TompkinsCountyData.csv",
        "./TompkinsCountyData.csv",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    raise FileNotFoundError(f"TompkinsCountyData.csv not found in any of these locations: {possible_paths}")


def geometry_to_polygon(geom):
    """Convert geometry string to Polygon object"""
    if pd.isna(geom) or geom is None:
        return None
    try:
        geom = ast.literal_eval(geom)
        if geom and "rings" in geom:
            return Polygon(geom.get("rings")[0])
        return None
    except (ValueError, SyntaxError, TypeError):
        return None


def extract_land_assessment_features(apartments_for_rent):
    """
    Extract land assessment features by joining with Tompkins County parcel data.
    
    Args:
        apartments_for_rent: DataFrame with listing data including latitude, longitude, and SQ_FT columns
        
    Returns:
        DataFrame with added assessment features:
        - LAND: Land assessment value
        - ASMT: Total assessment value
        - SQFT_parcel: Square footage from parcel data
        - SQFT_best: Best available square footage (parcel or apartment)
        - SQFT_filled: KNN-imputed square footage
        - assessment_per_sqft: Assessment per square foot
        - land_per_sqft: Land value per square foot
    """
    print("🏛️ Extracting land assessment features...")
    
    try:
        csv_path = get_tompkins_county_data_path()
        print(f"📂 Loading parcel data from: {csv_path}")
        parcels_df = gpd.read_file(csv_path)
        
        print("🔄 Converting geometry to polygons...")
        parcels_df["geometry"] = parcels_df["geometry"].apply(geometry_to_polygon)
        
        parcels_df = parcels_df[parcels_df["geometry"].notna()].copy()
        
        parcels_gdf = gpd.GeoDataFrame(parcels_df, geometry="geometry", crs="EPSG:3857")
        parcels_gdf = parcels_gdf.to_crs("EPSG:4326")
        
        print(f"✅ Loaded {len(parcels_gdf)} parcels")
        
        parcels_assessment_data_gdf = parcels_gdf[["LAND", "ASMT", "SQ_FT", "geometry"]].copy()
        parcels_assessment_data_gdf.rename(columns={"SQ_FT": "SQFT_parcel"}, inplace=True)
        
        apartments_for_rent_bounded = apartments_for_rent.copy()
        
        if "SQ_FT" in apartments_for_rent_bounded.columns:
            apartments_for_rent_bounded.rename(columns={"SQ_FT": "SQFT_apartment"}, inplace=True)
        elif "assessment_sqft" in apartments_for_rent_bounded.columns:
            apartments_for_rent_bounded.rename(columns={"assessment_sqft": "SQFT_apartment"}, inplace=True)
        else:
            apartments_for_rent_bounded["SQFT_apartment"] = np.nan
        
        if "geometry" not in apartments_for_rent_bounded.columns:
            if "latitude" in apartments_for_rent_bounded.columns and "longitude" in apartments_for_rent_bounded.columns:
                apartments_for_rent_bounded = gpd.GeoDataFrame(
                    apartments_for_rent_bounded,
                    geometry=gpd.points_from_xy(
                        apartments_for_rent_bounded.longitude,
                        apartments_for_rent_bounded.latitude
                    ),
                    crs="EPSG:4326"
                )
            else:
                print("⚠️ No geometry or lat/lng columns found, skipping spatial join")
                return apartments_for_rent
        
        print("🔗 Performing spatial join with parcel data...")
        apartments_for_rent_bounded = apartments_for_rent_bounded.sjoin(
            parcels_assessment_data_gdf, how="left", predicate="within"
        )
        
        apartments_for_rent_bounded = apartments_for_rent_bounded.drop(
            columns=['index_right'], errors='ignore'
        )
        
        initial_count = len(apartments_for_rent_bounded)
        apartments_for_rent_bounded = apartments_for_rent_bounded.dropna(subset=["LAND", "ASMT"])
        matched_count = len(apartments_for_rent_bounded)
        print(f"✅ Matched {matched_count}/{initial_count} listings with assessment data")
        
        if matched_count == 0:
            print("⚠️ No listings matched with assessment data, returning original DataFrame")
            return apartments_for_rent
        
        apartments_for_rent_bounded["SQFT_best"] = apartments_for_rent_bounded["SQFT_parcel"]
        mask = apartments_for_rent_bounded["SQFT_best"].isna()
        apartments_for_rent_bounded.loc[mask, "SQFT_best"] = apartments_for_rent_bounded.loc[mask, "SQFT_apartment"]
        
        apartments_for_rent_bounded["SQFT_best"] = pd.to_numeric(apartments_for_rent_bounded["SQFT_best"], errors='coerce')
        apartments_for_rent_bounded["LAND"] = pd.to_numeric(apartments_for_rent_bounded["LAND"], errors='coerce')
        apartments_for_rent_bounded["ASMT"] = pd.to_numeric(apartments_for_rent_bounded["ASMT"], errors='coerce')
        
        apartments_for_rent_bounded = apartments_for_rent_bounded.drop_duplicates(subset=["ListingId"], keep='first')
        apartments_for_rent_bounded = apartments_for_rent_bounded.reset_index(drop=True)
        
        print("🔧 Performing KNN imputation for missing square footage...")
        apartments_for_rent_bounded["SQFT_best"] = apartments_for_rent_bounded["SQFT_best"].replace(0, np.nan)
        
        impute_features = [
            "SQFT_best",
            "available_bedrooms",
            "available_bathrooms",
            "rent_per_person",
            "ASMT",
            "LAND",
            "latitude",
            "longitude"
        ]
        
        available_impute_features = [f for f in impute_features if f in apartments_for_rent_bounded.columns]
        
        if len(available_impute_features) < 3:
            print("⚠️ Not enough features for KNN imputation, skipping")
            apartments_for_rent_bounded["SQFT_filled"] = apartments_for_rent_bounded["SQFT_best"]
        else:
            impute_data = apartments_for_rent_bounded[available_impute_features].copy()
            
            impute_data = impute_data.fillna(0)
            
            imputer = KNNImputer(n_neighbors=5)
            imputed = imputer.fit_transform(impute_data)
            
            sqft_idx = available_impute_features.index("SQFT_best") if "SQFT_best" in available_impute_features else 0
            apartments_for_rent_bounded["SQFT_filled"] = imputed[:, sqft_idx]
        
        apartments_for_rent_bounded["SQFT_filled"] = pd.to_numeric(apartments_for_rent_bounded["SQFT_filled"], errors='coerce')
        
        print("📊 Calculating derived assessment features...")
        apartments_for_rent_bounded["assessment_per_sqft"] = (
            apartments_for_rent_bounded["ASMT"] / apartments_for_rent_bounded["SQFT_filled"]
        ).replace([np.inf, -np.inf], np.nan)
        
        apartments_for_rent_bounded["land_per_sqft"] = (
            apartments_for_rent_bounded["LAND"] / apartments_for_rent_bounded["SQFT_filled"]
        ).replace([np.inf, -np.inf], np.nan)
        
        print("🏷️ Creating submarket clusters...")
        try:
            if "geometry" not in apartments_for_rent_bounded.columns:
                if "latitude" in apartments_for_rent_bounded.columns and "longitude" in apartments_for_rent_bounded.columns:
                    apartments_for_rent_bounded = gpd.GeoDataFrame(
                        apartments_for_rent_bounded,
                        geometry=gpd.points_from_xy(
                            apartments_for_rent_bounded.longitude,
                            apartments_for_rent_bounded.latitude
                        ),
                        crs="EPSG:4326"
                    )
                else:
                    print("⚠️ No geometry or lat/lng for submarket clustering, skipping")
            
            apartments_m = apartments_for_rent_bounded.to_crs(3857)
            
            apartments_m['x_meters'] = apartments_m.geometry.x
            apartments_m['y_meters'] = apartments_m.geometry.y
            
            valid_coords = apartments_m[['x_meters', 'y_meters']].dropna()
            
            if len(valid_coords) > 6:  # Need at least 6 points for 6 clusters
                coords = valid_coords[['x_meters', 'y_meters']].values
                kmeans = KMeans(n_clusters=6, random_state=42, n_init=10).fit(coords)
                
                apartments_m['submarket'] = np.nan
                
                apartments_m.loc[valid_coords.index, 'submarket'] = kmeans.labels_
                
                apartments_for_rent_bounded = apartments_m.to_crs(apartments_for_rent_bounded.crs if hasattr(apartments_for_rent_bounded, 'crs') else 'EPSG:4326')
                
                if 'submarket' in apartments_for_rent_bounded.columns:
                    apartments_for_rent_bounded['submarket'] = apartments_for_rent_bounded['submarket'].astype('Int64')
                    print(f"   ✅ Created submarket clusters for {apartments_for_rent_bounded['submarket'].notna().sum()} listings")
                else:
                    print("   ⚠️ Failed to create submarket column")
            else:
                print(f"   ⚠️ Not enough valid coordinates ({len(valid_coords)}) for clustering, skipping")
        except Exception as e:
            print(f"   ⚠️ Error creating submarket clusters: {e}")
            import traceback
            traceback.print_exc()
        
        if "geometry" in apartments_for_rent_bounded.columns and "geometry" not in apartments_for_rent.columns:
            apartments_for_rent_bounded = apartments_for_rent_bounded.drop(columns=['geometry'])
        
        apartments_for_rent_bounded = apartments_for_rent_bounded.drop(columns=['x_meters', 'y_meters'], errors='ignore')
        
        print(f"✅ Successfully added assessment features to {len(apartments_for_rent_bounded)} listings")
        
        return apartments_for_rent_bounded
        
    except FileNotFoundError as e:
        print(f"⚠️ {e}")
        print("⚠️ Skipping land assessment feature extraction")
        return apartments_for_rent
    except Exception as e:
        print(f"⚠️ Error extracting land assessment features: {e}")
        import traceback
        traceback.print_exc()
        print("⚠️ Returning original DataFrame without assessment features")
        return apartments_for_rent


