"""
Transit Score Calculation Module

Calculates transit accessibility scores for housing listings using TCAT GTFS data
and adds nearest stop information.
"""
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
    
    # Filter apartments with valid coordinates
    valid_coords = apartments_for_rent['latitude'].notna() & apartments_for_rent['longitude'].notna()
    valid_apartments = apartments_for_rent[valid_coords].copy()
    
    if len(valid_apartments) == 0:
        print("⚠️ No valid coordinates found for transit score calculation")
        apartments_for_rent['transit_score'] = None
        apartments_for_rent['nearest_stop_name'] = None
        apartments_for_rent['walk_time_to_nearest_stop'] = None
        return apartments_for_rent
    
    try:
        # Determine GTFS file location
        MODEL_PATH = str("/opt/airflow/model")
        if not os.path.exists(MODEL_PATH):
            MODEL_PATH = str(Path(__file__).resolve().parent)
        
        gtfs_file = os.path.join(MODEL_PATH, "tcat_gtfs_final.zip")
        
        # Download GTFS if not exists
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
        
        # Extract GTFS components
        trips_df = feed.trips
        routes_df = feed.routes
        stop_times_df = feed.stop_times
        
        # Create stops GeoDataFrame
        stops_gdf = gpd.GeoDataFrame(
            feed.stops,
            geometry=gpd.points_from_xy(feed.stops.stop_lon, feed.stops.stop_lat),
            crs="EPSG:4326"
        )
        print(f"📍 Loaded {len(stops_gdf)} transit stops")
        
        print("🗺️ Building transit network...")
        stop_times_trips = stop_times_df.merge(trips_df, on="trip_id", how="left")
        st_routes = stop_times_trips.merge(routes_df, on="route_id", how="left")
        network_df = st_routes.merge(stops_gdf, on="stop_id", how="left")
        
        network_df = network_df.sort_values(["trip_id", "stop_sequence"]).reset_index(drop=True)
        network_df["next_stop_id"] = network_df.groupby("trip_id")["stop_id"].shift(-1)
        network_df["next_arrival_time"] = network_df.groupby("trip_id")["arrival_time"].shift(-1)
        
        network_df["travel_time_sec"] = (
            pd.to_timedelta(network_df["next_arrival_time"]) -
            pd.to_timedelta(network_df["departure_time"])
        ).dt.total_seconds()
        
        network_df = network_df.dropna(subset=["next_stop_id", "travel_time_sec"])
        
        G = nx.DiGraph()
        for _, row in network_df.iterrows():
            G.add_edge(
                row["stop_id"],
                row["next_stop_id"],
                weight=row["travel_time_sec"],
                route=row["route_id"]
            )
        print(f"✅ Transit network built with {G.number_of_nodes()} stops and {G.number_of_edges()} connections")
        
        def find_nearest_stop(lat, lon, stops_df):
            """Find the nearest bus stop and calculate walk time"""
            if pd.isna(lat) or pd.isna(lon):
                return {
                    "nearest_stop_name": None,
                    "nearest_stop_id": None,
                    "walk_time_to_nearest_stop": None
                }
            
            stops_df_copy = stops_df.copy()
            stops_df_copy["distance_meters"] = stops_df_copy.apply(
                lambda row: geopy.distance.geodesic((lat, lon), (row["stop_lat"], row["stop_lon"])).meters,
                axis=1
            )
            
            if len(stops_df_copy) == 0:
                return {
                    "nearest_stop_name": None,
                    "nearest_stop_id": None,
                    "walk_time_to_nearest_stop": None
                }
            
            nearest_stop = stops_df_copy.loc[stops_df_copy["distance_meters"].idxmin()]
            # Walking speed ~78 meters/min (5 km/h)
            walk_time_min = nearest_stop["distance_meters"] / 78.0
            
            return {
                "nearest_stop_name": nearest_stop["stop_name"],
                "nearest_stop_id": nearest_stop["stop_id"],
                "walk_time_to_nearest_stop": round(walk_time_min, 2)
            }
        
        print("🚶 Finding nearest stops for apartments...")
        nearest_stop_data = valid_apartments.apply(
            lambda row: find_nearest_stop(row["latitude"], row["longitude"], stops_gdf),
            axis=1
        )
        nearest_stop_df = pd.DataFrame(nearest_stop_data.tolist(), index=valid_apartments.index)
        valid_apartments = pd.concat([valid_apartments, nearest_stop_df], axis=1)
        
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
        
        def compute_transit_time(origin_stop_id, dest_stop_id, graph):
            """Calculate shortest transit time between two stops"""
            if pd.isna(origin_stop_id) or dest_stop_id is None:
                return np.inf
            
            try:
                travel_times = nx.single_source_dijkstra_path_length(graph, origin_stop_id, weight="weight")
                return travel_times.get(dest_stop_id, np.inf)
            except Exception:
                return np.inf
        
        print("⏱️ Computing transit times to destinations...")
        for name, dest_stop_id in destination_stops.items():
            col = f"transit_time_to_{name}"
            valid_apartments[col] = valid_apartments["nearest_stop_id"].apply(
                lambda origin_id: compute_transit_time(origin_id, dest_stop_id, G)
            )
            # Convert from seconds to minutes
            valid_apartments[col] = valid_apartments[col] / 60.0
        
        def impedance_function(time_minutes, beta=0.1):
            """Negative exponential impedance function"""
            if pd.isna(time_minutes) or np.isinf(time_minutes):
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
            if pd.notna(walk_time) and np.isfinite(walk_time):
                total += impedance_function(walk_time, 0.5) 
            
            return total
        
        print("📊 Calculating accessibility scores...")
        valid_apartments["accessibility_score"] = valid_apartments.apply(
            lambda row: get_accessibility_score(row, destinations),
            axis=1
        )
        
        max_score = valid_apartments["accessibility_score"].max()
        min_score = valid_apartments["accessibility_score"].min()
        
        if max_score > min_score:
            valid_apartments["transit_score"] = (
                (valid_apartments["accessibility_score"] - min_score) / (max_score - min_score) * 100
            ).round(2)
        else:
            valid_apartments["transit_score"] = 50.0 
        
        columns_to_merge = ["ListingId", "transit_score", "nearest_stop_name", "walk_time_to_nearest_stop"]
        
        for name in destinations.keys():
            col = f"transit_time_to_{name}"
            if col in valid_apartments.columns:
                columns_to_merge.append(col)
        
        apartments_for_rent = apartments_for_rent.merge(
            valid_apartments[columns_to_merge],
            on="ListingId",
            how="left",
            suffixes=("", "_new")
        )
        
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