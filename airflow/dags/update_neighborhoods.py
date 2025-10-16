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

import extract_rental_data

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
    df = df.rename(columns={
        'listingid': 'ListingId'
    })
    
    # Create Coordinates column from latitude/longitude
    print("📍 Creating Coordinates column from latitude/longitude")
    df['Coordinates'] = df.apply(
        lambda row: f'{{"lng": {row["longitude"]}, "lat": {row["latitude"]}}}'
        if pd.notna(row["longitude"]) and pd.notna(row["latitude"]) else None,
        axis=1
    )
    
    # Debug: Check coordinate data
    valid_coords = df["Coordinates"].notna()
    print(f"📍 Listings with valid coordinates: {valid_coords.sum()}/{len(df)}")
    
    if valid_coords.sum() > 0:
        print(f"📍 Sample coordinates:")
        sample_df = df[valid_coords].head(3)
        for _, row in sample_df.iterrows():
            print(f"  Listing {row['ListingId']}: {row['Coordinates']}")
    else:
        print("❌ No listings have valid coordinates in the database!")
        print("Sample data:")
        print(df[['ListingId', 'latitude', 'longitude', 'Coordinates']].head())
    
    return df


def update_neighborhoods():
    """
    Update neighborhoods for all current listings
    """
    print("🚀 Starting neighborhoods update process...")
    
    # Fetch current listings
    listings_df = fetch_current_listings()
    
    if listings_df.empty:
        print("⚠️ No listings found in database")
        return
    
    print(f"📊 Processing {len(listings_df)} listings")
    
    # Extract neighborhoods for all listings
    print("🏘️ Extracting neighborhoods...")
    try:
        updated_df = extract_rental_data.extract_neighborhood(listings_df)
        
        if 'neighborhood' not in updated_df.columns:
            print("❌ Neighborhood column not found in result")
            return
        
        non_null_count = updated_df['neighborhood'].notna().sum()
        print(f"📊 neighborhood: {non_null_count}/{len(updated_df)} non-null values")
        
        if non_null_count > 0:
            print(f"   Sample neighborhoods: {updated_df['neighborhood'].dropna().head(10).tolist()}")
            unique_neighborhoods = updated_df['neighborhood'].dropna().unique()
            print(f"   Unique neighborhoods found: {len(unique_neighborhoods)}")
            print(f"   Neighborhoods: {sorted(unique_neighborhoods)}")
        else:
            print("⚠️ No neighborhoods were extracted")
        
    except Exception as e:
        print(f"❌ Error extracting neighborhoods: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Update database with new neighborhoods
    update_database_neighborhoods(updated_df)
    
    print("✅ Neighborhoods update completed successfully!")


def update_database_neighborhoods(df):
    """
    Update the database with new neighborhood data for existing listings
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
            
            # Build update query for neighborhood field
            values = {}
            
            if pd.notna(row.get('neighborhood')):
                values['neighborhood'] = str(row['neighborhood'])
                values['listing_id'] = int(listing_id)
                
                update_query = """
                UPDATE housing_listings 
                SET neighborhood = :neighborhood
                WHERE listingid = :listing_id
                """
                
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
    
    print(f"✅ Updated neighborhood data for {updated_count} listings in database")
    if skipped_count > 0:
        print(f"⚠️ Skipped {skipped_count} listings with no valid neighborhood data")


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "update_neighborhoods",
    default_args=default_args,
    description="Update neighborhoods for all current listings",
    schedule_interval="0 5 * * 0",  # Run weekly on Sundays at 5 AM
    catchup=False
)

update_neighborhoods_task = PythonOperator(
    task_id="update_neighborhoods",
    python_callable=update_neighborhoods,
    execution_timeout=timedelta(minutes=30),  # Allow 30 minutes for neighborhood extraction
    dag=dag,
)

