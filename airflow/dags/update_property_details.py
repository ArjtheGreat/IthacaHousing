from airflow.decorators import dag, task
from pendulum import datetime, duration
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

import landlord_extraction

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
    
    print("📋 Fetching existing listings from database...")
    query = """
        SELECT listingid, listingaddress
        FROM housing_listings
        WHERE latitude IS NOT NULL 
        AND longitude IS NOT NULL
    """

    with engine.connect() as conn:
        df = pd.read_sql(query, conn.connection)
        
    print(f"✅ Fetched {len(df)} current listings from database")
    
    # Rename columns to match expected format
    df = df.rename(columns={'listingid': 'ListingId'})
    
    return df


def update_property_details():
    """
    Update property details for all current listings
    """
    print("🚀 Starting property details update process...")
    
    listings_df = fetch_current_listings()
    
    if listings_df.empty:
        print("⚠️ No listings found in database")
        return
    
    print(f"📊 Processing {len(listings_df)} listings")
    
    print("🏠 Adding property details from assessment data...")
    try:
        updated_df = landlord_extraction.add_property_details(listings_df)
        
        property_columns = {
            'NEIGHB': 'Neighborhood',
            'DEPTH': 'Depth',
            'FRONTAGE': 'Frontage',
            'ACRES': 'Acres',
            'PC': 'PC',
            'WATER': 'Water',
            'SEWER': 'Sewer',
            'SWRESNAME': 'Sewer Name',
            'YR_BUILT': 'Year Built',
            'SALE_PRICE': 'Sale Price',
            'SQ_FT': 'Square Feet'
        }
        
        for col, label in property_columns.items():
            if col in updated_df.columns:
                non_null_count = updated_df[col].notna().sum()
                print(f"📊 {label}: {non_null_count}/{len(updated_df)} non-null values")
                
                if non_null_count > 0 and col in ['YR_BUILT', 'SALE_PRICE', 'SQ_FT']:
                    print(f"   Range: {updated_df[col].min():.2f} - {updated_df[col].max():.2f}")
                    print(f"   Mean: {updated_df[col].mean():.2f}")
        
        property_count = sum(updated_df[col].notna().sum() for col in property_columns.keys() if col in updated_df.columns)
        if property_count == 0:
            print("⚠️ No valid property details were added")
        
    except Exception as e:
        print(f"❌ Error adding property details: {e}")
        import traceback
        traceback.print_exc()
        return
    
    update_database_property_details(updated_df)
    
    print("✅ Property details update completed successfully!")


def update_database_property_details(df):
    """
    Update the database with new property details for existing listings
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
    error_count = 0
    
    # Process each row in its own transaction to avoid transaction abort issues
    for _, row in df.iterrows():
        listing_id = row['ListingId']
        
        # Build update query dynamically based on available columns
        update_parts = []
        values = {}
        
        # Map property detail columns to database columns
        property_mappings = {
            'neighborhood_assessment': 'neighborhood_assessment',
            'property_depth': 'property_depth',
            'property_frontage': 'property_frontage',
            'property_acres': 'property_acres',
            'property_pc': 'property_pc',
            'water_access': 'water_access',
            'sewer_access': 'sewer_access',
            'sewer_name': 'sewer_name',
            'year_built': 'year_built',
            'sale_price': 'sale_price',
            'assessment_sqft': 'assessment_sqft'
        }
        
        for col, db_col in property_mappings.items():
            if col in df.columns and pd.notna(row[col]):
                value = row[col]
                if col in ['year_built'] and pd.notna(value):
                    value = int(value) if value > 0 else None
                elif col in ['sale_price', 'assessment_sqft', 'property_acres', 'property_depth', 'property_frontage'] and pd.notna(value):
                    value = float(value) if value > 0 else None
                elif col == 'neighborhood_assessment' and pd.notna(value):
                    value = int(value) if value > 0 else None
                elif col == 'property_pc' and pd.notna(value):
                    value = str(value) 
                
                if value is not None:
                    update_parts.append(f"{db_col} = :{col}")
                    values[col] = value
        
        if update_parts:
            update_query = f"""
            UPDATE housing_listings 
            SET {', '.join(update_parts)}
            WHERE listingid = :listing_id
            """
            values['listing_id'] = int(listing_id)
            
            # Use individual transaction for each update
            try:
                with engine.begin() as conn:
                    result = conn.execute(text(update_query), values)
                    if result.rowcount > 0:
                        updated_count += 1
                    else:
                        print(f"⚠️ No rows updated for listing {listing_id}")
            except Exception as e:
                print(f"❌ Error updating listing {listing_id}: {e}")
                print(f"   Query: {update_query}")
                print(f"   Values: {values}")
                error_count += 1
        else:
            skipped_count += 1
    
    print(f"✅ Updated property details for {updated_count} listings in database")
    if skipped_count > 0:
        print(f"⚠️ Skipped {skipped_count} listings with no valid property detail data")
    if error_count > 0:
        print(f"❌ Failed to update {error_count} listings due to errors")


@dag(
    dag_id="update_property_details",
    start_date=datetime(2025, 1, 1),
    schedule="0 6 * * 0",  # Run weekly on Sundays at 6 AM
    catchup=False,
    description="Update property details for all current listings",
    default_args={"owner": "airflow", "retries": 1, "retry_delay": duration(minutes=5)},
    tags=["property", "details", "weekly"]
)
def update_property_details_dag():
    
    @task(
        execution_timeout=duration(minutes=30)  # Allow 30 minutes for property details update
    )
    def update_property_details_task():
        return update_property_details()

    # Execute the task
    update_property_details_task()


# Instantiate the DAG
update_property_details_dag()
