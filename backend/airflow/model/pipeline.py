import pandas as pd
import fetch_housing_data
import calculate_amenity_score
import calculate_travel_times_distance
import calculate_transit_score
import data_preprocessing
import extract_safety_features
import model_training
import comparative_market_analysis
import extract_rental_data
import insert_into_postgredb
from sqlalchemy import create_engine, text
import os


DATA_PATH = "./insert_into_postgres.csv"

def get_existing_listing_ids():
    """
    Get all existing listing IDs from the database
    """
    DB_URI = os.getenv("DB_URI")
    if not DB_URI:
        return set()
    
    engine = create_engine(DB_URI)
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT listingid FROM housing_listings"))
            existing_ids = {row[0] for row in result}
            print(f"📊 Found {len(existing_ids)} existing listings in database")
            return existing_ids
    except Exception as e:
        print(f"⚠️ Error fetching existing listings: {e}")
        return set()

def get_existing_calculated_data():
    """
    Fetch existing calculated fields for all listings to preserve them
    """
    DB_URI = os.getenv("DB_URI")
    if not DB_URI:
        return pd.DataFrame()
    
    engine = create_engine(DB_URI)
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT listingid, walk_time, walk_routes, bike_time, bike_routes, 
                       drive_time, drive_routes, transit_score, amenities_score,
                       overallsafetyratingpct, nearest_neighbor_listingids
                FROM housing_listings
            """)
            result = conn.execute(query)
            existing_data = pd.DataFrame(result.fetchall(), columns=result.keys())
            print(f"📊 Fetched calculated data for {len(existing_data)} existing listings")
            return existing_data
    except Exception as e:
        print(f"⚠️ Error fetching existing calculated data: {e}")
        return pd.DataFrame()

def housing_data_pipeline():
    """
    Optimized Pipeline for Data Preprocessing for Apache Airflow
    
    Part 1: Fetch Data
    Part 2: Process only NEW listings (skip expensive operations for existing ones)
    Part 3: Pre-process and transform data for ALL listings
    Part 4: Run ML model and CMA for ALL listings (recalibration)
    Part 5: Insert/Update database
    """
    
    print("🚀 Starting optimized housing data pipeline...")
    
    print("📥 Fetching housing data...")
    apartments_for_rent = fetch_housing_data.housing_data_preprocessing()
    apartments_for_rent = extract_rental_data.extract_rental_data(apartments_for_rent)
    
    existing_ids = get_existing_listing_ids()
    existing_calculated_data = get_existing_calculated_data()
    
    new_listings = apartments_for_rent[~apartments_for_rent['ListingId'].isin(existing_ids)]
    existing_listings = apartments_for_rent[apartments_for_rent['ListingId'].isin(existing_ids)]
    
    print(f"🆕 Processing {len(new_listings)} new listings")
    print(f"♻️ Preserving calculated data for {len(existing_listings)} existing listings")
    
    if len(new_listings) > 0:        
        print("🗺️ Calculating travel times for new listings...")
        new_listings = calculate_travel_times_distance.compute_all_travel_times(new_listings)
        
        print("🚌 Calculating transit scores for new listings...")
        new_listings = calculate_transit_score.calculate_transit_score(new_listings)
        
        print("🏠 Calculating amenity scores for new listings...")
        new_listings = calculate_amenity_score.calculate_amenity_score(new_listings)
        
        print("🛡️ Calculating safety scores for new listings...")
        new_listings = extract_safety_features.calculate_safety_score(new_listings)
    
    if len(existing_listings) > 0 and len(existing_calculated_data) > 0:
        print("🔄 Merging preserved calculated data into existing listings...")
        existing_listings = existing_listings.merge(
            existing_calculated_data, 
            left_on='ListingId', 
            right_on='listingid', 
            how='left',
            suffixes=('', '_existing')
        )
        
        calc_fields = ['walk_time', 'walk_routes', 'bike_time', 'bike_routes', 
                      'drive_time', 'drive_routes', 'transit_score', 'amenities_score',
                      'overallsafetyratingpct', 'nearest_neighbor_listingids']
        
        for field in calc_fields:
            if f'{field}_existing' in existing_listings.columns:
                existing_listings[field] = existing_listings[f'{field}_existing'].fillna(existing_listings[field])
                existing_listings.drop(columns=[f'{field}_existing'], inplace=True)
        
        existing_listings.drop(columns=['listingid'], inplace=True, errors='ignore')
    
    apartments_for_rent = pd.concat([new_listings, existing_listings], ignore_index=True)
    
    print(f"📊 Total listings ready for model processing: {len(apartments_for_rent)}")

    print("🧹 Preprocessing data for model training...")
    X, y = model_training.define_X_Y_variables(apartments_for_rent)
    X, y = data_preprocessing.clean_up_x_y(X, y)
    X = data_preprocessing.median_mode_imputation(X)
    y = data_preprocessing.log_transform_prices(y)

    print("🤖 Training models and generating predictions for all listings...")
    apartments_for_rent = model_training.train_and_evaluate_models(X, y, apartments_for_rent)

    print("📈 Performing comparative market analysis for all listings...")
    X_for_cma = comparative_market_analysis.define_X_for_cma(apartments_for_rent)
    apartments_for_rent = comparative_market_analysis.perform_cma(X_for_cma, apartments_for_rent)

    print("💾 Inserting data into database...")
    insert_into_postgredb.psql_insert_copy(apartments_for_rent)
    insert_into_postgredb.confirmation()