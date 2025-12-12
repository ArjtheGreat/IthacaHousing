import pandas as pd
import numpy as np
import os
from pathlib import Path
import geopandas as gpd


def get_poi_file_path(filename):
    """Get the path to a POI CSV file, trying multiple locations"""
    BASE_DIR = "/opt/airflow/model"
    if not os.path.exists(BASE_DIR):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    possible_paths = [
        os.path.join(BASE_DIR, "data", filename),
        f"/opt/airflow/model/data/{filename}",
        f"/opt/airflow/model/{filename}",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", filename),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), filename),
        f"./data/{filename}",
        f"./{filename}",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None  


def load_poi(path):
    """Load POI data from CSV and convert to GeoDataFrame in EPSG:3857"""
    if path is None or not os.path.exists(path):
        return None
    
    df = pd.read_csv(path)

    possible_lat_cols = ["latitude", "lat", "location/lat"]
    possible_lon_cols = ["longitude", "lon", "location/lng"]

    lat_col = next((c for c in possible_lat_cols if c in df.columns), None)
    lon_col = next((c for c in possible_lon_cols if c in df.columns), None)

    if lat_col is None or lon_col is None:
        print(f"⚠️ Could not find lat/lon columns in {path}, skipping")
        return None

    df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
    df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")

    df = df.dropna(subset=[lat_col, lon_col])
    
    if len(df) == 0:
        print(f"⚠️ No valid coordinates in {path}, skipping")
        return None

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
        crs="EPSG:4326"
    )

    return gdf.to_crs(3857)


def extract_poi_features(apartments_for_rent, buffer_distance=200):
    """
    Extract Point of Interest (POI) features by calculating counts and distances.
    
    Args:
        apartments_for_rent: DataFrame with listing data including latitude, longitude
        buffer_distance: Distance in meters for counting POIs (default: 200m)
        
    Returns:
        DataFrame with added POI features:
        - {poi_type}_count_200m: Count of POIs within buffer_distance
        - {poi_type}_nearest_dist: Distance to nearest POI in meters
        Where poi_type is: food, attractions, shopping, grocery
    """
    print("📍 Extracting Point of Interest (POI) features...")
    
    try:
        # Load POI data
        poi_files = {
            "food": "Food_Drinks.csv",
            "attractions": "Attractions.csv",
            "shopping": "Shopping.csv",
            "grocery": "Groceries_ConvinienceStores.csv",
        }
        
        pois = {}
        for name, filename in poi_files.items():
            poi_path = get_poi_file_path(filename)
            if poi_path:
                print(f"📂 Loading {name} POIs from: {poi_path}")
                poi_gdf = load_poi(poi_path)
                if poi_gdf is not None and len(poi_gdf) > 0:
                    pois[name] = poi_gdf
                    print(f"   ✅ Loaded {len(poi_gdf)} {name} POIs")
                else:
                    print(f"   ⚠️ No valid {name} POIs found")
            else:
                print(f"   ⚠️ {filename} not found, skipping {name} POIs")
        
        if not pois:
            print("⚠️ No POI data found, skipping POI feature extraction")
            return apartments_for_rent
        
        apartments_poi = apartments_for_rent.copy()
        
        if "geometry" not in apartments_poi.columns:
            if "latitude" in apartments_poi.columns and "longitude" in apartments_poi.columns:
                apartments_poi = gpd.GeoDataFrame(
                    apartments_poi,
                    geometry=gpd.points_from_xy(
                        apartments_poi.longitude,
                        apartments_poi.latitude
                    ),
                    crs="EPSG:4326"
                )
            else:
                print("⚠️ No geometry or lat/lng columns found, skipping POI features")
                return apartments_for_rent
        
        print(f"🔄 Converting to EPSG:3857 for distance calculations...")
        apartments_m = apartments_poi.to_crs(3857)
        
        print(f"📊 Calculating POI features (buffer: {buffer_distance}m)...")
        for name, poi_gdf in pois.items():
            print(f"   Processing {name} POIs...")
            
            apartments_m[f"{name}_count_{buffer_distance}m"] = apartments_m.geometry.apply(
                lambda x: poi_gdf.distance(x).lt(buffer_distance).sum() if pd.notna(x) else 0
            )
            
            apartments_m[f"{name}_nearest_dist"] = apartments_m.geometry.apply(
                lambda x: poi_gdf.distance(x).min() if pd.notna(x) else np.nan
            )
            
            print(f"      ✅ Added {name}_count_{buffer_distance}m and {name}_nearest_dist")
        
        apartments_poi = apartments_m.to_crs(4326)
        
        if "geometry" not in apartments_for_rent.columns:
            apartments_poi = apartments_poi.drop(columns=['geometry'])
        
        print(f"✅ Successfully added POI features to {len(apartments_poi)} listings")
        
        return apartments_poi
        
    except Exception as e:
        print(f"⚠️ Error extracting POI features: {e}")
        import traceback
        traceback.print_exc()
        print("⚠️ Returning original DataFrame without POI features")
        return apartments_for_rent

