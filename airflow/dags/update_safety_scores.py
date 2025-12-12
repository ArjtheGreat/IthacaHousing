from airflow.decorators import dag, task
from pendulum import datetime, duration
import pandas as pd
from sqlalchemy import create_engine, text
import os
from pathlib import Path

# Ensure __file__ is a string for path operations
current_file = str(__file__) if isinstance(__file__, bytes) else __file__
dag_dir = Path(current_file).parent.parent
model_dir = dag_dir / "model"

# Add model directory to path
import sys
sys.path.append(str(model_dir))

from core.fetch_housing_data import fetch_active_listings
from extractors.extract_safety_features import extract_safety_features

# Database connection
DB_URI = os.getenv("DB_URI", "postgresql://postgres:password@localhost:5432/ithaca_housing")

@dag(
    dag_id="update_safety_scores",
    start_date=datetime(2024, 1, 1),
    schedule="0 4 * * 0",  # Run weekly on Sundays at 4 AM
    catchup=False,
    description="Update safety scores and certificate compliance for all current listings",
    default_args={"owner": "airflow", "retries": 1, "retry_delay": duration(minutes=5)},
    tags=["safety", "weekly"]
)
def update_safety_scores_dag():
    
    @task
    def update_safety_scores():
        """
        Update safety scores by fetching fresh data from Cornell Off-Campus Housing
        and mapping SafetyRatings to existing listings in the database
        """
        print("🔒 Starting safety scores update...")
        
        try:
            # Create database engine
            engine = create_engine(DB_URI)
        
            # 1. Fetch fresh data from Cornell Off-Campus Housing
            print("📡 Fetching fresh data from Cornell Off-Campus Housing...")
            fresh_data = fetch_active_listings()
            
            if fresh_data is None or len(fresh_data) == 0:
                print("⚠️ No fresh data fetched from Cornell")
                return
            
            print(f"📊 Fetched {len(fresh_data)} listings from Cornell")
            
            # 2. Extract SafetyRatings from fresh data
            print("🔍 Extracting SafetyRatings from fresh data...")
            
            # Create a mapping of listingid -> SafetyRatings
            safety_mapping = {}
            
            for _, row in fresh_data.iterrows():
                if pd.notna(row.get('SafetyRatings')):
                    try:
                        # Extract safety features for this listing
                        safety_features = extract_safety_features(row['SafetyRatings'])
                        
                        # Check if Valid Certificate of Compliance exists
                        if 'Valid Certificate of Compliance' in safety_features:
                            cert_value = safety_features['Valid Certificate of Compliance']
                            
                            # Apply mapping: 8 -> 1, NaN -> 0
                            if pd.notna(cert_value) and cert_value == 8:
                                mapped_value = 1
                            elif pd.notna(cert_value):
                                mapped_value = int(cert_value)
                            else:
                                mapped_value = 0
                            
                            safety_mapping[row['ListingId']] = mapped_value
                            
                    except Exception as e:
                        print(f"⚠️ Error processing SafetyRatings for listing {row['ListingId']}: {e}")
                        continue
            
            print(f"🔍 Extracted safety data for {len(safety_mapping)} listings")
            
            # 3. Get existing listings from database
            print("📋 Fetching existing listings from database...")
            query = """
                SELECT listingid, valid_certificate_of_compliance
                FROM housing_listings
                WHERE latitude IS NOT NULL 
                AND longitude IS NOT NULL
            """
            
            with engine.connect() as conn:
                existing_listings = pd.read_sql(query, conn.connection)
            
            print(f"📊 Found {len(existing_listings)} existing listings")
            
            # 4. Update database with new safety scores
            print("💾 Updating database with new safety scores...")
            
            def update_listing_safety(listing_id, cert_value):
                try:
                    with engine.begin() as conn:
                        update_query = text("""
                            UPDATE housing_listings 
                            SET valid_certificate_of_compliance = :valid_certificate_of_compliance
                            WHERE listingid = :listingid
                        """)
                        
                        conn.execute(update_query, {
                            'listingid': listing_id,
                            'valid_certificate_of_compliance': cert_value
                        })
                        
                    return True
                except Exception as e:
                    print(f"❌ Failed to update listing {listing_id}: {e}")
                    return False
            
            # Apply updates
            success_count = 0
            updated_count = 0
            total_mappings = len(safety_mapping)
            
            for listing_id, cert_value in safety_mapping.items():
                if update_listing_safety(listing_id, cert_value):
                    success_count += 1
                    if cert_value == 1:  # Count how many got valid certificates
                        updated_count += 1
            
            print(f"✅ Successfully updated {success_count}/{total_mappings} listings")
            
            # Print summary statistics
            valid_count = updated_count
            invalid_count = success_count - updated_count
            print(f"📈 Safety Summary:")
            print(f"   - Valid certificates: {valid_count}")
            print(f"   - Invalid certificates: {invalid_count}")
            print(f"   - Valid percentage: {(valid_count/success_count)*100:.1f}%" if success_count > 0 else "   - Valid percentage: 0.0%")
            
        except Exception as e:
            print(f"❌ Error updating safety scores: {e}")
            raise

    # Execute the task
    update_safety_scores()


# Instantiate the DAG
update_safety_scores_dag()
