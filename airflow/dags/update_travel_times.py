from airflow.decorators import dag, task
from pendulum import datetime, duration
import sys
import os
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text

MODEL_PATH = "/opt/airflow/model"

if not os.path.exists(MODEL_PATH):
    MODEL_PATH = str(Path(__file__).resolve().parent.parent / "model")

if MODEL_PATH not in sys.path:
    sys.path.append(MODEL_PATH)

import calculators.calculate_travel_times_distance as calculate_travel_times_distance

os.environ['NO_PROXY'] = '*'

def fetch_current_listings():
    """
    Fetch all current listings from the database
    """
    DB_URI = os.getenv("DB_URI")
    
    engine = create_engine(
        DB_URI,
        pool_pre_ping=True,
        pool_recycle=1800, 
        pool_size=1,     
        max_overflow=0,       
        connect_args={
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5
        }
    )
    
    query = """
    SELECT listingid, listingaddress, listingcity, listingzip, 
           latitude, longitude, rentamount, bedrooms, bathrooms,
           available_bedrooms, available_bathrooms, housingtype,
           shortdescription, pets, amenities, listingphotos
    FROM housing_listings
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    """
    
    with engine.connect() as conn:
        df = pd.read_sql(query, conn.connection)
    
    print(f"✅ Fetched {len(df)} current listings from database")
    return df


def compute_travel_times_fixed(apartments_for_rent, graphs):
    """
    Fixed version of travel time computation that properly handles array lengths
    """
    import networkx as nx
    import osmnx as ox
    
    CAMPUS_POINTS = [
        {"name": "Uris Hall",        "lat": 42.4472,   "lon": -76.4822 },
        {"name": "Agriculture Quad", "lat": 42.448796, "lon": -76.478018},
        {"name": "Arts Quad",        "lat": 42.448966, "lon": -76.484175},
        {"name": "Engineering Quad", "lat": 42.444668, "lon": -76.482570},
    ]
    
    # Create a copy to avoid modifying the original
    result_df = apartments_for_rent.copy()
    
    for mode, G in graphs.items():
        if G is None:
            print(f"⚠️ No {mode} graph available — skipping.")
            continue

        print(f"\n🚶‍♂️ Processing mode: {mode}")

        try:
            valid_mask = apartments_for_rent["longitude"].notna() & apartments_for_rent["latitude"].notna()
            apartment_nodes = ox.distance.nearest_nodes(
                G,
                apartments_for_rent.loc[valid_mask, "longitude"],
                apartments_for_rent.loc[valid_mask, "latitude"]
            )
        except Exception as e:
            print(f"⚠️ Failed to map apartment nodes for {mode}: {e}")
            continue

        for ref in CAMPUS_POINTS:
            ref_name = ref["name"].replace(" ", "")
            ref_lat, ref_lon = ref["lat"], ref["lon"]
            print(f"  → Computing travel times to {ref['name']}")

            try:
                ref_node = ox.distance.nearest_nodes(G, ref_lon, ref_lat)
            except Exception as e:
                print(f"⚠️ Could not find {ref['name']} node: {e}")
                result_df[f"{mode}_time_{ref_name}"] = [None] * len(apartments_for_rent)
                continue

            # Initialize times array with None for all apartments
            times = [None] * len(apartments_for_rent)
            
            # Calculate times only for valid apartments
            valid_indices = apartments_for_rent.index[valid_mask]
            for i, apt_node in enumerate(apartment_nodes):
                try:
                    time_min = nx.shortest_path_length(G, apt_node, ref_node, weight="travel_time") / 60
                    if mode == "drive":
                        time_min *= 1.8
                    times[valid_indices[i]] = round(time_min, 2)
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    times[valid_indices[i]] = None
                except Exception as e:
                    print(f"❌ Failed route to {ref['name']}: {e}")
                    times[valid_indices[i]] = None

            result_df[f"{mode}_time_{ref_name}"] = times

    return result_df

def update_travel_times():
    """
    Update travel times for all current listings
    """
    print("🚀 Starting travel times update process...")
    
    # Fetch current listings
    listings_df = fetch_current_listings()
    
    if listings_df.empty:
        print("⚠️ No listings found in database")
        return
    
    print(f"📊 Processing {len(listings_df)} listings")
    print(f"Sample coordinates: lat={listings_df['latitude'].iloc[0]}, lon={listings_df['longitude'].iloc[0]}")
    
    # Build graphs for different transportation modes
    print("🗺️ Building transportation graphs...")
    try:
        graphs = calculate_travel_times_distance.build_graphs()
        print(f"✅ Built graphs for modes: {list(graphs.keys())}")
        
        # Check if any graphs failed to build
        failed_graphs = [mode for mode, graph in graphs.items() if graph is None]
        if failed_graphs:
            print(f"⚠️ Failed to build graphs for: {failed_graphs}")
    except Exception as e:
        print(f"❌ Error building graphs: {e}")
        return
    
    # Compute travel times for all listings
    print("⏱️ Computing travel times...")
    try:
        updated_df = compute_travel_times_fixed(listings_df, graphs)
        
        # Debug: Check if travel time columns were created
        travel_time_cols = [col for col in updated_df.columns if 'time' in col]
        print(f"📋 Travel time columns created: {travel_time_cols}")
        
        # Debug: Check for non-null values
        for col in travel_time_cols:
            non_null_count = updated_df[col].notna().sum()
            print(f"📊 {col}: {non_null_count}/{len(updated_df)} non-null values")
            if non_null_count > 0:
                print(f"   Sample values: {updated_df[col].dropna().head(3).tolist()}")
        
    except Exception as e:
        print(f"❌ Error computing travel times: {e}")
        return
    
    # Update database with new travel times
    update_database_travel_times(updated_df)
    
    print("✅ Travel times update completed successfully!")

def update_database_travel_times(df):
    """
    Update the database with new travel times for existing listings
    """
    DB_URI = os.getenv("DB_URI")
    
    engine = create_engine(
        DB_URI,
        pool_pre_ping=True,
        pool_recycle=1800, 
        pool_size=1,     
        max_overflow=0,       
        connect_args={
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5
        }
    )
    
    # Define travel time columns (matching actual generated column names)
    travel_time_columns = [
        "walk_time_UrisHall", "walk_time_AgricultureQuad", "walk_time_ArtsQuad", "walk_time_EngineeringQuad",
        "bike_time_UrisHall", "bike_time_AgricultureQuad", "bike_time_ArtsQuad", "bike_time_EngineeringQuad", 
        "drive_time_UrisHall", "drive_time_AgricultureQuad", "drive_time_ArtsQuad", "drive_time_EngineeringQuad"
    ]
    
    updated_count = 0
    skipped_count = 0
    
    # Debug: Check what columns are actually available
    print(f"📋 Available columns in DataFrame: {list(df.columns)}")
    print(f"📋 Looking for travel time columns: {travel_time_columns}")
    
    # Check which travel time columns exist
    existing_travel_cols = [col for col in travel_time_columns if col in df.columns]
    print(f"📋 Found travel time columns: {existing_travel_cols}")
    
    with engine.begin() as conn:
        for _, row in df.iterrows():
            listing_id = row['listingid']
            
            # Build update query for travel times
            update_parts = []
            values = {}
            
            for col in travel_time_columns:
                if col in df.columns and pd.notna(row[col]):
                    # Map generated column names to database column names (lowercase)
                    db_col = col.lower()
                    update_parts.append(f"{db_col} = :{col}")
                    values[col] = float(row[col]) if pd.notna(row[col]) else None
                elif col in df.columns:
                    print(f"🔍 Column {col} exists but value is null: {row[col]}")
                else:
                    print(f"❌ Column {col} not found in DataFrame")
            
            if update_parts:
                update_query = f"""
                UPDATE housing_listings 
                SET {', '.join(update_parts)}
                WHERE listingid = :listing_id
                """
                values['listing_id'] = int(listing_id)
                
                try:
                    result = conn.execute(text(update_query), values)
                    if result.rowcount > 0:
                        updated_count += 1
                    else:
                        print(f"⚠️ No rows updated for listing {listing_id}")
                except Exception as e:
                    print(f"❌ Error updating listing {listing_id}: {e}")
            else:
                skipped_count += 1
                print(f"⚠️ Skipping listing {listing_id} - no valid travel time data")
    
    print(f"✅ Updated travel times for {updated_count} listings in database")
    if skipped_count > 0:
        print(f"⚠️ Skipped {skipped_count} listings with no valid travel time data")

@dag(
    dag_id="update_travel_times",
    start_date=datetime(2025, 1, 1),
    schedule="0 2 * * *",  # Run daily at 2 AM
    catchup=False,
    description="Update travel times for all current listings",
    default_args={"owner": "airflow", "retries": 1, "retry_delay": duration(minutes=5)},
    tags=["travel", "times", "daily"]
)
def update_travel_times_dag():
    
    @task(
        execution_timeout=duration(minutes=30)  # Allow more time for travel time calculations
    )
    def update_travel_times_task():
        return update_travel_times()

    # Execute the task
    update_travel_times_task()


# Instantiate the DAG
update_travel_times_dag()
