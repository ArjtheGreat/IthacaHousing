import numpy as np
import pandas as pd
import geopy.distance
import pandas as pd
import geopandas as gpd
import numpy as np
import networkx as nx
import geopy.distance
import requests
import os
from pathlib import Path

def calculate_transit_score(apartments_for_rent):
    """
    Calculate comprehensive transit metrics for apartments including:
    - transit_score: Overall accessibility score (0-100)
    - nearest_stop_name: Name of the closest bus stop
    - walk_time_to_nearest_stop: Walk time to nearest stop in minutes
    
    Args:
        apartments_for_rent (pd.DataFrame): DataFrame with ListingId, latitude, longitude columns
    
    Returns:
        pd.DataFrame: Input dataframe with added transit-related columns
    """
    try:
        import gtfs_kit as gk
    except ImportError:
        print("⚠️ gtfs_kit not installed. Skipping transit score calculation.")
        apartments_for_rent['transit_score'] = None
        apartments_for_rent['nearest_stop_name'] = None
        apartments_for_rent['walk_time_to_nearest_stop'] = None
        return apartments_for_rent
    
    print("🚌 Starting transit score calculation...")
    
    try:
        # Determine GTFS file location
        MODEL_PATH = str("/opt/airflow/model")
        if not os.path.exists(MODEL_PATH):
            MODEL_PATH = str(Path(__file__).resolve().parent)
        
        gtfs_file = os.path.join(MODEL_PATH, "tcat_gtfs_final.zip")
        
        if not os.path.exists(gtfs_file):
            print("📥 Downloading latest TCAT GTFS data...")
            gtfs_url = "https://s3.amazonaws.com/tcat-gtfs/tcat-ny-us.zip"
            response = requests.get(gtfs_url, timeout=30)
            response.raise_for_status()
            
            with open(gtfs_file, "wb") as f:
                f.write(response.content)
            print(f"✅ Downloaded GTFS data to {gtfs_file}")
        else:
            print(f"📂 Using existing GTFS data: {gtfs_file}")
        
        # Load GTFS feed
        print("📖 Loading GTFS feed...")
        feed = gk.read_feed(gtfs_file, dist_units="km")
        
        stops_gdf = gpd.GeoDataFrame(
            feed.stops,
            geometry=gpd.points_from_xy(feed.stops.stop_lon, feed.stops.stop_lat),
            crs="EPSG:4326"
        )
        
        # --- Load travel times ---
        travel_times_path = os.path.join(MODEL_PATH, "StopsToCornellDestinations.csv")

        travel_times_df = pd.read_csv(travel_times_path)
        
        def find_nearest_stop(lat, lon, stops_df):
            """
            Finds the nearest bus stop based on latitude and longitude.

            Returns:
            - stop_name: Name of the closest bus stop.
            - distance_meters: Distance to the stop.
            """
            stops_df_modified = stops_df.copy()
            stops_df_modified["distance_meters"] = stops_df_modified.apply(
                lambda row: geopy.distance.geodesic((lat, lon), (row["stop_lat"], row["stop_lon"])).meters, axis=1
            )

            nearest_stop = stops_df_modified.loc[stops_df_modified["distance_meters"].idxmin()]
            return {
                "nearest_stop_name": nearest_stop["stop_name"],
                "nearest_stop_id": nearest_stop["stop_id"],
                "geometry": nearest_stop["geometry"],
                "distance_meters": nearest_stop["distance_meters"],
                "walk_time_to_nearest_stop": nearest_stop["distance_meters"] / 78
            }

        
        print("🚶 Finding nearest stops for apartments...")
        apartments_for_rent["nearest_stop"] = apartments_for_rent.apply(
            lambda x: find_nearest_stop(x["latitude"], x["longitude"], stops_gdf),
            axis=1
        )
        extacted_nearest_stop_df = pd.json_normalize(apartments_for_rent["nearest_stop"])
        apartments_for_rent = pd.concat([apartments_for_rent, extacted_nearest_stop_df], axis=1)

        destinations = {
            "ag_quad": {"coords": (42.448796, -76.478018), "opportunity": 1.0},
            "arts_quad": {"coords": (42.448966, -76.484175), "opportunity": 1.0},
            "eng_quad": {"coords": (42.444668, -76.482570), "opportunity": 1.0},
        }
        
        destination_stops = {}
        for name, info in destinations.items():
            lat, lon = info["coords"]
            dest_stop_info = find_nearest_stop(lat, lon, stops_gdf)
            destination_stops[name] = dest_stop_info["nearest_stop_id"]
        
        print(f"🎯 Calculated destination stops: {list(destination_stops.keys())}")
        
        def compute_transit_time(origin_stop_id, dest_stop_id):
          """Return the travel time (in seconds) between two stops, or np.inf if missing."""
          if pd.isna(origin_stop_id) or dest_stop_id is None:
              return np.inf

          origin_stop_id = int(origin_stop_id)

          try:
              match = travel_times_df.loc[
                  (travel_times_df["from_id"] == origin_stop_id)
                  & (travel_times_df["to_id"] == dest_stop_id),
                  "travel_time",
              ]
              if not match.empty:
                  return float(match.iloc[0]) 
              else:
                  return np.inf
          except Exception:
              return np.inf

        
        print("⏱️ Computing transit times to destinations...")
        for name, dest_stop_id in destination_stops.items():
            col = f"transit_time_to_{name}"
            apartments_for_rent[col] = apartments_for_rent["nearest_stop_id"].apply(
                lambda origin_id: compute_transit_time(origin_id, name)
            )
            # Keep original values in minutes (no division by 60)
        
        def impedance_function(time_minutes, beta=0.1):
            """Negative exponential impedance function"""
            if(time_minutes == np.nan):
              return 0.0
            return np.exp(-beta * time_minutes)
        
        def get_accessibility_score(row, destinations):
            """Compute accessibility score as sum of opportunity * impedance"""
            total = 0.0
            
            for name, info in destinations.items():
                time_col = f"transit_time_to_{name}"
                if time_col in row:
                    time = row[time_col]
                    if np.isfinite(time):
                        total += info["opportunity"] * impedance_function(time)
            
            walk_time = row.get("walk_time_to_nearest_stop")
            total += impedance_function(walk_time, 0.5) 
            
            return total
        
        print("📊 Calculating accessibility scores...")
        apartments_for_rent["accessibility_score"] = apartments_for_rent.apply(
            lambda row: get_accessibility_score(row, destinations),
            axis=1
        )
        
        max_score = apartments_for_rent["accessibility_score"].max()
        min_score = apartments_for_rent["accessibility_score"].min()
        
        if max_score > min_score:
            apartments_for_rent["transit_score"] = (
                (apartments_for_rent["accessibility_score"] - min_score) / (max_score - min_score) * 100
            ).round(2)
        else:
            apartments_for_rent["transit_score"] = 50.0 
        
        columns_to_merge = ["ListingId", "transit_score", "nearest_stop_name", "walk_time_to_nearest_stop"]
        
        for name in destinations.keys():
            col = f"transit_time_to_{name}"
            if col in apartments_for_rent.columns:
                columns_to_merge.append(col)
        
        all_transit_cols = ["transit_score", "nearest_stop_name", "walk_time_to_nearest_stop", 
                           "transit_time_to_ag_quad", "transit_time_to_arts_quad", "transit_time_to_eng_quad"]
        
        for col in all_transit_cols:
            if f"{col}_new" in apartments_for_rent.columns:
                apartments_for_rent[col] = apartments_for_rent[f"{col}_new"].fillna(apartments_for_rent.get(col))
                apartments_for_rent.drop(columns=[f"{col}_new"], inplace=True)
        
        apartments_for_rent.drop(columns=["accessibility_score"], errors='ignore', inplace=True)
                
        non_null_count = apartments_for_rent['transit_score'].notna().sum()
        print(f"✅ Transit scores calculated for {non_null_count}/{len(apartments_for_rent)} listings")
        
        if non_null_count > 0:
            print(f"   Score range: {apartments_for_rent['transit_score'].min():.1f} - {apartments_for_rent['transit_score'].max():.1f}")
            print(f"   Mean score: {apartments_for_rent['transit_score'].mean():.1f}")
        
    except Exception as e:
        print(f"❌ Error calculating transit scores: {e}")
        import traceback
        traceback.print_exc()
        apartments_for_rent['transit_score'] = None
        apartments_for_rent['nearest_stop_name'] = None
        apartments_for_rent['walk_time_to_nearest_stop'] = None
    
    return apartments_for_rent