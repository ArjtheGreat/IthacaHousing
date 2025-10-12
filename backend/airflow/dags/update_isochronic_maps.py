from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import pandas as pd
import os
import sys
from pathlib import Path

# Add the model directory to the path
current_file = str(__file__) if isinstance(__file__, bytes) else __file__
MODEL_PATH = str(Path(current_file).resolve().parent.parent / "model")
if not os.path.exists(MODEL_PATH):
    MODEL_PATH = str(Path(current_file).resolve().parent.parent / "model")

sys.path.append(MODEL_PATH)

import calculate_travel_times_distance
from sqlalchemy import create_engine, text

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    "update_isochronic_maps",
    default_args=default_args,
    description="Update isochronic maps for all current listings",
    schedule_interval="0 2 * * 0",  # Run weekly on Sundays at 2 AM
    catchup=False
)

def update_isochronic_maps():
    """
    Update isochronic maps for all listings in the database
    """
    print("🗺️ Starting isochronic maps update...")
    
    # Get database connection
    DB_URI = os.getenv("DB_URI")
    if not DB_URI:
        raise ValueError("DB_URI environment variable not set")
    
    engine = create_engine(DB_URI)
    
    try:
        # Fetch all listings from database
        print("📊 Fetching listings from database...")
        query = """
            SELECT listingid, listingaddress, listingcity, listingzip, createdate, shortdescription,
                   rentamount, renttype, pets, amenities, bedrooms, bathrooms, available_bedrooms,
                   available_bathrooms, housingtype, latitude, longitude, listingphotos, transit_score, 
                   amenities_score, overallsafetyratingpct, predictedrent, differenceinfairvalue, 
                   predicted_rent_cma, nearest_neighbor_listingids, rent_per_person, num_people, 
                   total_rent_amount, owner_name, nearest_stop_name, walk_time_to_nearest_stop, 
                   transit_time_to_ag_quad, transit_time_to_arts_quad, transit_time_to_eng_quad,
                   walk_time_urishall, walk_time_agriculturequad, walk_time_artsquad, walk_time_engineeringquad,
                   bike_time_urishall, bike_time_agriculturequad, bike_time_artsquad, bike_time_engineeringquad,
                   drive_time_urishall, drive_time_agriculturequad, drive_time_artsquad, drive_time_engineeringquad
            FROM housing_listings
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        """
        with engine.connect() as conn:
            df = pd.read_sql(query, conn.connection)

        print(f"📋 Found {len(df)} listings with valid coordinates")
        
        if len(df) == 0:
            print("⚠️ No listings found with valid coordinates")
            return
        
        # Rename columns to match expected format
        df = df.rename(columns={
            'listingid': 'ListingId',
            'listingaddress': 'ListingAddress',
            'listingcity': 'ListingCity',
            'listingzip': 'ListingZip',
            'createdate': 'CreateDate',
            'shortdescription': 'ShortDescription',
            'rentamount': 'RentAmount',
            'renttype': 'RentType',
            'pets': 'Pets',
            'amenities': 'Amenities',
            'bedrooms': 'Bedrooms',
            'bathrooms': 'Bathrooms',
            'available_bedrooms': 'available_bedrooms',
            'available_bathrooms': 'available_bathrooms',
            'housingtype': 'HousingType',
            'latitude': 'latitude',
            'longitude': 'longitude',
            'listingphotos': 'ListingPhotos'
        })
        
        print("🗺️ Calculating isochronic maps...")
        df_with_isochrones = calculate_travel_times_distance.make_isochronic_map(df)
        
        # Update database with isochronic data
        print("💾 Updating database with isochronic maps...")
        
        def update_listing_isochrones(row):
            """Update isochronic data for a single listing"""
            try:
                with engine.begin() as conn:
                    update_query = text("""
                        UPDATE housing_listings 
                        SET iso15 = :iso15
                        WHERE listingid = :listingid
                    """)
                    
                    conn.execute(update_query, {
                        'listingid': row['ListingId'],
                        'iso15': row['iso15']
                    })
                    
                return True
            except Exception as e:
                print(f"❌ Failed to update listing {row['ListingId']}: {e}")
                return False
        
        # Update each listing
        success_count = 0
        for _, row in df_with_isochrones.iterrows():
            if update_listing_isochrones(row):
                success_count += 1
        
        print(f"✅ Successfully updated isochronic maps for {success_count}/{len(df_with_isochrones)} listings")
        
    except Exception as e:
        print(f"❌ Error updating isochronic maps: {e}")
        raise

# Define the task
update_isochronic_task = PythonOperator(
    task_id='update_isochronic_maps',
    python_callable=update_isochronic_maps,
    dag=dag,
)

# Set task dependencies
update_isochronic_task
