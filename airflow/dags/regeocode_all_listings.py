from airflow.decorators import dag, task
from pendulum import datetime, duration
import sys
import os
import pandas as pd
import time
from pathlib import Path
from sqlalchemy import create_engine, text

MODEL_PATH = "/opt/airflow/model"

if not os.path.exists(MODEL_PATH):
    current_file = str(__file__) if isinstance(__file__, bytes) else __file__
    MODEL_PATH = str(Path(current_file).resolve().parent.parent / "model")

if MODEL_PATH not in sys.path:
    sys.path.append(MODEL_PATH)

import core.geocoder as geocoder
from core.geocoder import move_directional_after_number  #

os.environ['NO_PROXY'] = '*'

@dag(
    dag_id="regeocode_all_listings",
    start_date=datetime(2024, 1, 1),
    schedule=None,  # Manual trigger only
    catchup=False,
    description="Re-geocode all listings using move_directional_after_number function",
    default_args={"owner": "airflow", "retries": 1, "retry_delay": duration(minutes=5)},
    tags=["geocoding", "maintenance", "database"]
)
def regeocode_all_listings():
    
    @task
    def fetch_all_listings():
        """
        Fetch all listings from the database that need re-geocoding.
        """
        print("📊 Fetching all listings from database...")
        
        DB_URI = os.getenv("DB_URI")
        if not DB_URI:
            raise ValueError("DB_URI environment variable not set")
        
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
                "keepalives_count": 5,
            }
        )
        
        query = text("""
            SELECT listingid, listingaddress, listingcity, listingzip, 
                   latitude, longitude
            FROM housing_listings
            ORDER BY listingid
        """)
        
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        
        print(f"✅ Fetched {len(df)} listings from database")
        print(f"   - Listings with existing coordinates: {df[['latitude', 'longitude']].notna().all(axis=1).sum()}")
        print(f"   - Listings without coordinates: {df[['latitude', 'longitude']].isna().any(axis=1).sum()}")
        
        # Convert to dict for XCom
        return df.to_dict(orient='records')
    
    @task
    def regeocode_listings(**context):
        """
        Re-geocode all listings using move_directional_after_number function.
        """
        print("🌍 Starting re-geocoding process...")
        
        # Get listings from previous task
        ti = context['ti']
        listings_data = ti.xcom_pull(task_ids='fetch_all_listings')
        listings_df = pd.DataFrame(listings_data)
        
        if listings_df.empty:
            print("⚠️ No listings to re-geocode")
            return {"updated": 0, "failed": 0, "skipped": 0}
        
        print(f"📋 Processing {len(listings_df)} listings...")
        
        # Prepare DataFrame for geocoding
        listings_df = listings_df.rename(columns={
            'listingid': 'ListingId',
            'listingaddress': 'ListingAddress',
            'listingcity': 'ListingCity',
            'listingzip': 'ListingZip'
        })
        
        # Track results
        updated_count = 0
        failed_count = 0
        skipped_count = 0
        results = []
        
        # Process each listing
        for idx, row in listings_df.iterrows():
            listing_id = row['ListingId']
            
            # Check if address would change with move_directional_after_number
            original_address = row['ListingAddress']
            if pd.isna(original_address) or original_address == '':
                print(f"⚠️ Skipping {listing_id}: no address")
                skipped_count += 1
                continue
            
            improved_address = move_directional_after_number(original_address)
            
            # Only geocode if the address actually changed
            if improved_address == original_address:
                print(f"⏭️  Skipping {listing_id}: address unchanged ('{original_address}')")
                skipped_count += 1
                continue
            
            print(f"📍 {listing_id}: '{original_address}' -> '{improved_address}'")
            
            try:
                coords = geocoder.get_coordinates({
                    'ListingAddress': original_address,
                    'ListingCity': row['ListingCity'],
                    'ListingZip': row['ListingZip']
                })
                
                if 'error' in coords:
                    print(f"❌ {listing_id}: Geocoding failed - {coords.get('message', coords.get('error'))}")
                    failed_count += 1
                    results.append({
                        'listingid': listing_id,
                        'latitude': None,
                        'longitude': None,
                        'status': 'failed',
                        'error': coords.get('message', coords.get('error'))
                    })
                else:
                    lat = coords.get('latitude')
                    lng = coords.get('longitude')
                    
                    if lat and lng:
                        print(f"✅ {listing_id}: ({lat}, {lng})")
                        updated_count += 1
                        results.append({
                            'listingid': listing_id,
                            'latitude': lat,
                            'longitude': lng,
                            'status': 'success'
                        })
                    else:
                        print(f"⚠️ {listing_id}: No coordinates returned")
                        failed_count += 1
                        results.append({
                            'listingid': listing_id,
                            'latitude': None,
                            'longitude': None,
                            'status': 'failed',
                            'error': 'No coordinates in response'
                        })
                
                # Rate limiting - be nice to Google API
                time.sleep(0.1)  # 100ms delay between requests
                
            except Exception as e:
                print(f"❌ {listing_id}: Exception during geocoding - {e}")
                failed_count += 1
                results.append({
                    'listingid': listing_id,
                    'latitude': None,
                    'longitude': None,
                    'status': 'failed',
                    'error': str(e)
                })
        
        print(f"\n📊 Re-geocoding Summary:")
        print(f"   ✅ Successfully geocoded: {updated_count}")
        print(f"   ❌ Failed: {failed_count}")
        print(f"   ⏭️  Skipped (no address change or no address): {skipped_count}")
        print(f"   📋 Total processed: {len(listings_df)}")
        
        # Convert results to DataFrame for next task
        results_df = pd.DataFrame(results)
        return results_df.to_dict(orient='records')
    
    @task
    def update_database_coordinates(**context):
        """
        Update the database with new coordinates.
        """
        print("💾 Updating database with new coordinates...")
        
        DB_URI = os.getenv("DB_URI")
        if not DB_URI:
            raise ValueError("DB_URI environment variable not set")
        
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
                "keepalives_count": 5,
            }
        )
        
        # Get results from previous task
        ti = context['ti']
        results_data = ti.xcom_pull(task_ids='regeocode_listings')
        results_df = pd.DataFrame(results_data)
        
        if results_df.empty:
            print("⚠️ No results to update")
            return
        
        # Filter to only successful geocodings
        successful_results = results_df[results_df['status'] == 'success'].copy()
        
        if successful_results.empty:
            print("⚠️ No successful geocodings to update")
            return
        
        print(f"📋 Updating {len(successful_results)} listings in database...")
        
        try:
            with engine.begin() as conn:
                update_query = text("""
                    UPDATE housing_listings
                    SET latitude = :latitude, longitude = :longitude
                    WHERE listingid = :listingid
                """)
                
                update_records = successful_results[['listingid', 'latitude', 'longitude']].to_dict(orient='records')
                
                # Execute updates in batches
                batch_size = 100
                total_updated = 0
                
                for i in range(0, len(update_records), batch_size):
                    batch = update_records[i:i + batch_size]
                    conn.execute(update_query, batch)
                    total_updated += len(batch)
                    print(f"   ✅ Updated batch {i//batch_size + 1}: {len(batch)} listings")
                
                print(f"✅ Successfully updated {total_updated} listings in database")
                
        except Exception as e:
            print(f"❌ Error updating database: {e}")
            import traceback
            traceback.print_exc()
            raise e
        finally:
            engine.dispose()
        
        # Print summary of failed geocodings
        failed_results = results_df[results_df['status'] == 'failed']
        if not failed_results.empty:
            print(f"\n⚠️ {len(failed_results)} listings failed to geocode:")
            for _, row in failed_results.head(10).iterrows():
                print(f"   - {row['listingid']}: {row.get('error', 'Unknown error')}")
            if len(failed_results) > 10:
                print(f"   ... and {len(failed_results) - 10} more")
    
    # Task dependencies
    listings = fetch_all_listings()
    results = regeocode_listings()
    update_db = update_database_coordinates()
    
    listings >> results >> update_db


# Instantiate the DAG
regeocode_all_listings()

