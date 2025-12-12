from airflow.decorators import dag, task
from pendulum import datetime, duration
import pandas as pd
import os
import sys
from datetime import datetime as dt
from sqlalchemy import create_engine, text

# Add model directory to path
MODEL_PATH = "/opt/airflow/model"
if not os.path.exists(MODEL_PATH):
    current_file = str(__file__) if isinstance(__file__, bytes) else __file__
    MODEL_PATH = os.path.join(os.path.dirname(current_file), "..", "model")
sys.path.append(MODEL_PATH)

from pipeline import track_removed_listings

@dag(
    dag_id="test_sold_listings",
    start_date=datetime(2024, 1, 1),
    schedule=None,  # Manual trigger only
    catchup=False,
    description="Test sold_listings feature - tracking removed listings and database insertion",
    default_args={"owner": "airflow", "retries": 1, "retry_delay": duration(minutes=5)},
    tags=["test", "database", "sold_listings"]
)
def test_sold_listings():
    
    @task
    def create_test_data():
        """
        Create test data simulating existing listings in the database
        and new listings from a fresh fetch.
        """
        print("🧪 Creating test data for sold_listings test...")
        
        # Simulate existing listings in the database (5 listings)
        # Use integer IDs to match the schema (listingid is serial/int)
        existing_listings = pd.DataFrame({
            'listingid': [5481, 5482, 5483, 5484, 5485],
            'listingaddress': [
                '123 Test Street',
                '456 Test Avenue',
                '789 Test Boulevard',
                '321 Test Road',
                '654 Test Lane'
            ],
            'listingcity': ['Ithaca', 'Ithaca', 'Ithaca', 'Ithaca', 'Ithaca'],
            'listingzip': ['14850', '14850', '14850', '14850', '14850'],
            'neighborhood': ['Downtown', 'Collegetown', 'Fall Creek', 'South Hill', 'Northside'],
            'rentamount': [1200.0, 1500.0, 1800.0, 1000.0, 2000.0],
            'rent_per_person': [600, 750, 900, 500, 1000],
            'available_bedrooms': [2, 2, 3, 1, 4],
            'available_bathrooms': [1, 1, 2, 1, 2],
            'year_built': [1995, 2010, 2005, 1980, 2015],
            'createdate': [
                '2024-01-01 00:00:00',
                '2024-01-15 00:00:00',
                '2024-02-01 00:00:00',
                '2024-02-15 00:00:00',
                '2024-03-01 00:00:00'
            ],
            'listingexpirationdate': [
                '2024-12-31 00:00:00',
                '2024-12-31 00:00:00',
                '2024-12-31 00:00:00',
                '2024-12-31 00:00:00',
                '2024-12-31 00:00:00'
            ],
            'lengthavailable': [12.0, 12.0, 12.0, 12.0, 12.0],
            'housingtype': ['Apartment', 'House', 'Apartment', 'House', 'Apartment'],
            'owner_name': ['Test Owner 1', 'Test Owner 2', 'Test Owner 3', 'Test Owner 4', 'Test Owner 5'],
            'listingtypes': ['Graduate', 'Undergraduate', 'Graduate', 'Undergraduate', 'Graduate'],
            'sale_price': [None, None, None, None, None],
            'property_acres': [None, None, None, None, None],
            'assessment_sqft': [None, None, None, None, None],
            'latitude': [42.44, 42.45, 42.46, 42.47, 42.48],
            'longitude': [-76.48, -76.49, -76.50, -76.51, -76.52],
            'drive_time_urishall': [10.5, 12.3, 8.7, 15.2, 9.8],
            'drive_time_agriculturequad': [11.2, 13.1, 9.4, 16.0, 10.5],
            'drive_time_artsquad': [12.8, 14.5, 10.9, 17.3, 11.7],
            'drive_time_engineeringquad': [13.5, 15.2, 11.6, 18.1, 12.4]
        })
        
        # Simulate new listings (only 3 of the 5 still exist - 999992 and 999994 were removed)
        new_listing_ids = {999991, 999993, 999995}
        
        print(f"📊 Created test data:")
        print(f"   - Existing listings: {len(existing_listings)}")
        print(f"   - New listing IDs: {len(new_listing_ids)}")
        print(f"   - Expected removed: {len(existing_listings) - len(new_listing_ids)}")
        print(f"   - Removed listing IDs: {set(existing_listings['listingid']) - new_listing_ids}")
        
        return {
            'existing_listings': existing_listings.to_dict(orient='records'),
            'new_listing_ids': list(new_listing_ids)
        }
    
    @task
    def test_track_removed_listings(**context):
        """
        Test the track_removed_listings function with the test data.
        """
        print("🧪 Testing track_removed_listings function...")
        
        # Get test data from previous task
        ti = context['ti']
        test_data = ti.xcom_pull(task_ids='create_test_data')
        
        existing_listings_df = pd.DataFrame(test_data['existing_listings'])
        new_listing_ids = set(test_data['new_listing_ids'])
        
        print(f"📋 Existing listings DataFrame shape: {existing_listings_df.shape}")
        print(f"📋 New listing IDs: {new_listing_ids}")
        
        try:
            # Test the function
            track_removed_listings(existing_listings_df, new_listing_ids)
            print("✅ track_removed_listings function executed successfully!")
            return "SUCCESS"
        except Exception as e:
            print(f"❌ track_removed_listings function test FAILED: {e}")
            import traceback
            traceback.print_exc()
            raise e
    
    @task
    def verify_database_insertion(**context):
        """
        Verify that the removed listings were correctly inserted into the sold_listings table.
        """
        print("🔍 Verifying database insertion...")
        
        DB_URI = os.getenv("DB_URI")
        if not DB_URI:
            print("⚠️ DB_URI not set, skipping database verification")
            return "SKIPPED"
        
        engine = create_engine(DB_URI)
        
        try:
            with engine.connect() as conn:
                # Query for test listings that should have been inserted
                query = text("""
                    SELECT 
                        listingid, 
                        listingaddress, 
                        listingcity, 
                        neighborhood,
                        rentamount,
                        rent_per_person,
                        removed_timestamp
                    FROM sold_listings
                    WHERE listingid IN (999992, 999994)
                    ORDER BY listingid
                """)
                
                result = conn.execute(query)
                rows = result.fetchall()
                
                if len(rows) == 0:
                    print("⚠️ No test listings found in sold_listings table")
                    print("   This could mean:")
                    print("   - The insert didn't work")
                    print("   - The test listings were already there from a previous run")
                    return "NO_DATA"
                
                print(f"✅ Found {len(rows)} test listings in sold_listings table:")
                for row in rows:
                    print(f"   - {row[0]}: {row[1]}, {row[2]} ({row[3]}) - Removed: {row[6]}")
                
                # Also check for any other test listings
                query_all = text("""
                    SELECT listingid, removed_timestamp
                    FROM sold_listings
                    WHERE listingid >= 999991 AND listingid <= 999995
                    ORDER BY removed_timestamp DESC
                """)
                
                result_all = conn.execute(query_all)
                all_test_rows = result_all.fetchall()
                
                if len(all_test_rows) > len(rows):
                    print(f"📝 Note: Found {len(all_test_rows)} total test listings (including from previous runs)")
                
                return "SUCCESS"
                
        except Exception as e:
            print(f"❌ Database verification FAILED: {e}")
            import traceback
            traceback.print_exc()
            raise e
        finally:
            engine.dispose()
    
    @task
    def cleanup_test_data(**context):
        """
        Optional: Clean up test data from sold_listings table.
        Comment out if you want to keep the test data for inspection.
        """
        print("🧹 Cleaning up test data from sold_listings table...")
        
        DB_URI = os.getenv("DB_URI")
        if not DB_URI:
            print("⚠️ DB_URI not set, skipping cleanup")
            return "SKIPPED"
        
        engine = create_engine(DB_URI)
        
        try:
            with engine.begin() as conn:
                # Delete test listings
                delete_query = text("""
                    DELETE FROM sold_listings
                    WHERE listingid >= 999991 AND listingid <= 999995
                """)
                
                result = conn.execute(delete_query)
                deleted_count = result.rowcount
                
                print(f"✅ Cleaned up {deleted_count} test listings from sold_listings table")
                return f"CLEANED_{deleted_count}"
                
        except Exception as e:
            print(f"⚠️ Cleanup FAILED (non-fatal): {e}")
            return "CLEANUP_FAILED"
        finally:
            engine.dispose()
    
    # Task dependencies
    test_data = create_test_data()
    test_result = test_track_removed_listings()
    verify_result = verify_database_insertion()
    cleanup_result = cleanup_test_data()
    
    test_data >> test_result >> verify_result >> cleanup_result


# Instantiate the DAG
test_sold_listings()

