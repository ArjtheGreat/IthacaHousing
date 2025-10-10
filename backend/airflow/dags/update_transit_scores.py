from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text

MODEL_PATH = "/opt/airflow/model"

if not os.path.exists(MODEL_PATH):
    current_file = str(__file__) if isinstance(__file__, bytes) else __file__
    MODEL_PATH = str(Path(current_file).resolve().parent.parent / "model")

if MODEL_PATH not in sys.path:
    sys.path.append(MODEL_PATH)

import calculate_transit_score

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
           latitude, longitude
    FROM housing_listings
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    """
    
    with engine.connect() as conn:
        df = pd.read_sql(query, conn.connection)
    
    print(f"✅ Fetched {len(df)} current listings from database")
    
    # Rename columns to match expected format
    df = df.rename(columns={'listingid': 'ListingId'})
    
    # Debug: Check coordinate data
    valid_coords = df["longitude"].notna() & df["latitude"].notna()
    print(f"📍 Listings with valid coordinates: {valid_coords.sum()}/{len(df)}")
    
    if valid_coords.sum() > 0:
        print(f"📍 Sample coordinates:")
        sample_df = df[valid_coords].head(3)
        for _, row in sample_df.iterrows():
            print(f"  Listing {row['ListingId']}: lat={row['latitude']}, lon={row['longitude']}")
    else:
        print("❌ No listings have valid coordinates in the database!")
        print("Sample data:")
        print(df[['ListingId', 'latitude', 'longitude']].head())
    
    return df


def update_transit_scores():
    """
    Update transit scores for all current listings
    """
    print("🚀 Starting transit scores update process...")
    
    # Fetch current listings
    listings_df = fetch_current_listings()
    
    if listings_df.empty:
        print("⚠️ No listings found in database")
        return
    
    print(f"📊 Processing {len(listings_df)} listings")
    
    # Compute transit scores for all listings
    print("🚌 Computing transit scores...")
    try:
        updated_df = calculate_transit_score.calculate_transit_score(listings_df)
        
        transit_columns = ['transit_score', 'nearest_stop_name', 'walk_time_to_nearest_stop',
                          'transit_time_to_ag_quad', 'transit_time_to_arts_quad', 'transit_time_to_eng_quad']
        missing_columns = [col for col in transit_columns if col not in updated_df.columns]
        
        if missing_columns:
            print(f"❌ Missing columns: {missing_columns}")
            return
        
        for col in transit_columns:
            non_null_count = updated_df[col].notna().sum()
            print(f"📊 {col}: {non_null_count}/{len(updated_df)} non-null values")
            
            if non_null_count > 0:
                if col in ['transit_score', 'walk_time_to_nearest_stop', 'transit_time_to_ag_quad', 
                          'transit_time_to_arts_quad', 'transit_time_to_eng_quad']:
                    print(f"   Sample values: {updated_df[col].dropna().head(3).tolist()}")
                    if updated_df[col].notna().any():
                        print(f"   Min: {updated_df[col].min():.2f}, Max: {updated_df[col].max():.2f}")
                elif col == 'nearest_stop_name':
                    print(f"   Sample stops: {updated_df[col].dropna().head(3).tolist()}")
        
    except Exception as e:
        print(f"❌ Error computing transit scores: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Update database with new transit scores
    update_database_transit_scores(updated_df)
    
    print("✅ Transit scores update completed successfully!")


def update_database_transit_scores(df):
    """
    Update the database with new transit scores and nearest stop info for existing listings
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
    
    updated_count = 0
    skipped_count = 0
    
    with engine.begin() as conn:
        for _, row in df.iterrows():
            listing_id = row['ListingId']
            
            # Build update query for transit fields
            update_parts = []
            values = {}
            
            if pd.notna(row.get('transit_score')):
                update_parts.append("transit_score = :transit_score")
                values['transit_score'] = float(row['transit_score'])
            
            if pd.notna(row.get('nearest_stop_name')):
                update_parts.append("nearest_stop_name = :nearest_stop_name")
                values['nearest_stop_name'] = str(row['nearest_stop_name'])
            
            if pd.notna(row.get('walk_time_to_nearest_stop')):
                update_parts.append("walk_time_to_nearest_stop = :walk_time_to_nearest_stop")
                values['walk_time_to_nearest_stop'] = float(row['walk_time_to_nearest_stop'])
            
            if pd.notna(row.get('transit_time_to_ag_quad')):
                update_parts.append("transit_time_to_ag_quad = :transit_time_to_ag_quad")
                values['transit_time_to_ag_quad'] = float(row['transit_time_to_ag_quad'])
            
            if pd.notna(row.get('transit_time_to_arts_quad')):
                update_parts.append("transit_time_to_arts_quad = :transit_time_to_arts_quad")
                values['transit_time_to_arts_quad'] = float(row['transit_time_to_arts_quad'])
            
            if pd.notna(row.get('transit_time_to_eng_quad')):
                update_parts.append("transit_time_to_eng_quad = :transit_time_to_eng_quad")
                values['transit_time_to_eng_quad'] = float(row['transit_time_to_eng_quad'])
            
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
    
    print(f"✅ Updated transit data for {updated_count} listings in database")
    if skipped_count > 0:
        print(f"⚠️ Skipped {skipped_count} listings with no valid transit data")


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "update_transit_scores",
    default_args=default_args,
    description="Update transit scores for all current listings",
    schedule_interval="0 3 * * 0",  # Run weekly on Sundays at 3 AM
    catchup=False
)

update_transit_scores_task = PythonOperator(
    task_id="update_transit_scores",
    python_callable=update_transit_scores,
    execution_timeout=timedelta(hours=1),  # Allow 1 hour for transit score calculations
    dag=dag,
)

