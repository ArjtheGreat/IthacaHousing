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
import landlord_extraction
import insert_into_postgredb
import pipeline_metrics
from sqlalchemy import create_engine, text
import os


DATA_PATH = "./insert_into_postgres.csv"

DB_URI = os.getenv("DB_URI")
engine = create_engine(DB_URI) if DB_URI else None


def get_existing_listing_ids():
    """
    Get all existing listing IDs from the database
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT listingid FROM housing_listings"))
            existing_ids = {row[0] for row in result}
            print(f"📊 Found {len(existing_ids)} existing listings in database")
            return existing_ids
    except Exception as e:
        print(f"⚠️ Error fetching existing listings: {e}")
        return set()


def get_existing_listings_dataframe():
    """
    Fetch essential listing fields for tracking removals.
    """
    if engine is None:
        print("⚠️ Database engine not initialized; cannot fetch existing listings dataframe")
        return pd.DataFrame()

    try:
        with engine.connect() as conn:
            query = text("""
                SELECT listingid, listingaddress, listingcity, listingzip, neighborhood,
                       rentamount, rent_per_person, available_bedrooms, available_bathrooms,
                       year_built, createdate, listingexpirationdate
                FROM housing_listings
            """)
            result = conn.execute(query)
            listings_df = pd.DataFrame(result.fetchall(), columns=result.keys())
            print(f"📊 Loaded {len(listings_df)} existing listings with full details")
            return listings_df
    except Exception as e:
        print(f"⚠️ Error fetching existing listing details: {e}")
        return pd.DataFrame()

def get_existing_coordinates():
    """
    Fetch existing latitude/longitude coordinates from database to avoid re-geocoding.
    Returns a DataFrame with listingid, latitude, longitude.
    """
    if engine is None:
        print("⚠️ Database engine not initialized; cannot fetch existing coordinates")
        return pd.DataFrame()

    try:
        with engine.connect() as conn:
            query = text("""
                SELECT listingid, latitude, longitude
                FROM housing_listings
                WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            """)
            result = conn.execute(query)
            coords_df = pd.DataFrame(result.fetchall(), columns=result.keys())
            print(f"📍 Loaded {len(coords_df)} existing listings with coordinates")
            return coords_df
    except Exception as e:
        print(f"⚠️ Error fetching existing coordinates: {e}")
        return pd.DataFrame()

def get_existing_calculated_data():
    """
    Fetch existing calculated fields for all listings to preserve them
    """
    try:
        with engine.connect() as conn:
            table_info = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'housing_listings'
            """)).fetchall()
            existing_columns = [row[0] for row in table_info]
            
            base_columns = ['listingid', 'transit_score', 'amenities_score', 'valid_certificate_of_compliance', 'nearest_neighbor_listingids']
            new_travel_columns = [
                'walk_time_urishall', 'walk_time_agriculturequad', 'walk_time_artsquad', 'walk_time_engineeringquad',
                'bike_time_urishall', 'bike_time_agriculturequad', 'bike_time_artsquad', 'bike_time_engineeringquad',
                'drive_time_urishall', 'drive_time_agriculturequad', 'drive_time_artsquad', 'drive_time_engineeringquad'
            ]
            transit_columns = [
                'nearest_stop_name', 'walk_time_to_nearest_stop', 'transit_time_to_ag_quad', 
                'transit_time_to_arts_quad', 'transit_time_to_eng_quad'
            ]
            
            columns_to_select = [col for col in base_columns + new_travel_columns + transit_columns if col in existing_columns]
            
            if not columns_to_select:
                print("⚠️ No calculated columns found in database")
                return pd.DataFrame()
                
            query = text(f"""
                SELECT {', '.join(columns_to_select)}
                FROM housing_listings
            """)
            result = conn.execute(query)
            existing_data = pd.DataFrame(result.fetchall(), columns=result.keys())
            print(f"📊 Fetched calculated data for {len(existing_data)} existing listings")
            print(f"📊 Available columns: {columns_to_select}")
            return existing_data
    except Exception as e:
        print(f"⚠️ Error fetching existing calculated data: {e}")
        return pd.DataFrame()


def track_removed_listings(existing_df, new_ids: set):
    """
    Track listings removed between data pulls.
    Inserts metadata about removed listings into 'listings_removed'.
    
    Args:
        existing_df (pd.DataFrame): current listings table from DB before update
        new_ids (set): IDs of listings in the newly fetched dataset
    """
    if not isinstance(existing_df, pd.DataFrame):
        print(f"⚠️ Expected DataFrame but got {type(existing_df)}; skipping removed listing tracking")
        return
    
    if existing_df is None or existing_df.empty:
        print("⚠️ Existing listings dataframe is empty; skipping removed listing tracking")
        return

    if "listingid" not in existing_df.columns:
        print("⚠️ 'listingid' column not found in existing listings dataframe; skipping removed listing tracking")
        return

    existing_df = existing_df.copy()
    print(existing_df["listingid"])
    existing_df["listingid"] = existing_df["listingid"].astype(str)
    removed_df = existing_df[~existing_df["listingid"].isin(new_ids)]

    print(removed_df)
    if removed_df.empty:
        print("✅ No removed listings detected this run")
        return

    print(f"🗑️ Detected {len(removed_df)} removed listings - recording...")

    try:
        with engine.begin() as conn:
            insert_sql = text("""
                INSERT INTO sold_listings (
                    listingid, listingaddress, listingcity, listingzip, neighborhood,
                    rentamount, rent_per_person, available_bedrooms, available_bathrooms,
                    year_built, createdate, listingexpirationdate, removed_timestamp
                )
                VALUES (
                    :listingid, :listingaddress, :listingcity, :listingzip, :neighborhood,
                    :rentamount, :rent_per_person, :available_bedrooms, :available_bathrooms,
                    :year_built, :createdate, :listingexpirationdate, NOW()
                )
                ON CONFLICT (listingid)
                DO UPDATE SET removed_timestamp = EXCLUDED.removed_timestamp;
            """)

            conn.execute(insert_sql, removed_df.to_dict(orient="records"))

        print("✅ Removed listings recorded in sold_listings table")

    except Exception as e:
        print(f"⚠️ Error recording removed listings: {e}")
        import traceback
        traceback.print_exc()


def housing_data_pipeline():
    """
    Optimized Housing Insights ETL + ML Pipeline

    Stages:
    1. Fetch raw data
    2. Add safety, landlord, property, and neighborhood features
    3. Track removed listings
    4. Split new vs existing, process accordingly
    5. Merge preserved calculations for existing listings
    6. Compute amenities + rental features
    7. Prepare ML features (X, y)
    8. Train model + compute CMA
    9. Insert data + pipeline metrics
    """

    print("🚀 Starting Housing Data Pipeline")

    # ============================================================
    # 1) FETCH EXISTING COORDINATES (to avoid re-geocoding)
    # ============================================================
    print("📍 Fetching existing coordinates from database...")
    existing_coordinates = get_existing_coordinates()
    
    # ============================================================
    # 2) FETCH RAW DATA (with coordinate reuse)
    # ============================================================
    print("📥 Fetching rental data...")
    apartments_for_rent = fetch_housing_data.housing_data_preprocessing(existing_coordinates=existing_coordinates)

    print(apartments_for_rent["latitude"].head())

    print("🛡️ Adding safety features...")
    apartments_for_rent = extract_safety_features.calculate_safety_score(apartments_for_rent)

    print("👤 Extracting landlord + property info...")
    apartments_for_rent = landlord_extraction.extract_landlord_names(apartments_for_rent)
    apartments_for_rent = landlord_extraction.add_property_details(apartments_for_rent)

    print("📍 Extracting neighborhoods...")
    apartments_for_rent = extract_rental_data.extract_neighborhood(apartments_for_rent)

    print("🏗️ Adding property/structural features...")
    apartments_for_rent = data_preprocessing.add_property_features(apartments_for_rent)

    # ============================================================
    # 3) FETCH EXISTING DATA FROM DB
    # ============================================================
    existing_ids           = get_existing_listing_ids()
    existing_listings_df   = get_existing_listings_dataframe()
    existing_calculated    = get_existing_calculated_data()

    # ============================================================
    # 4) TRACK REMOVED LISTINGS
    # ============================================================
    try:
        new_ids = set(apartments_for_rent["ListingId"].dropna().astype(str))

        if isinstance(existing_listings_df, pd.DataFrame) and not existing_listings_df.empty:
            track_removed_listings(existing_listings_df, new_ids)
        else:
            print("⚠️ Skipping removed listing tracking (no existing listing details)")
    except Exception as e:
        print(f"⚠️ Failed to track removed listings: {e}")
        import traceback
        traceback.print_exc()

    # ============================================================
    # 5) SPLIT NEW VS EXISTING LISTINGS
    # ============================================================
    new_listings      = apartments_for_rent[~apartments_for_rent["ListingId"].isin(existing_ids)]
    existing_listings = apartments_for_rent[apartments_for_rent["ListingId"].isin(existing_ids)]

    print(f"🆕 New listings: {len(new_listings)}")
    print(f"♻️ Existing listings: {len(existing_listings)}")

    # ============================================================
    # 6) PROCESS NEW LISTINGS (expensive ops once)
    # ============================================================
    if len(new_listings) > 0:
        print("🗺️ Calculating travel times (new only)...")
        graphs = calculate_travel_times_distance.build_graphs()
        new_listings = calculate_travel_times_distance.compute_all_travel_times(new_listings, graphs)

        print("🗺️ Generating isochronic maps...")
        new_listings = calculate_travel_times_distance.make_isochronic_map(new_listings)

        print("🚌 Calculating transit scores...")
        new_listings = calculate_transit_score.calculate_transit_score(new_listings)

    # ============================================================
    # 7) MERGE PRESERVED CALCULATIONS FOR EXISTING LISTINGS
    # ============================================================
    if len(existing_listings) > 0 and len(existing_calculated) > 0:
        print("🔄 Merging preserved calculations...")

        existing_listings = existing_listings.merge(
            existing_calculated,
            left_on="ListingId",
            right_on="listingid",
            how="left",
            suffixes=("", "_existing")
        )

        calc_fields = [
            "transit_score", "amenities_score", "valid_certificate_of_compliance",
            "nearest_neighbor_listingids",
            "walk_time_urishall", "walk_time_agriculturequad", "walk_time_artsquad", "walk_time_engineeringquad",
            "bike_time_urishall", "bike_time_agriculturequad", "bike_time_artsquad", "bike_time_engineeringquad",
            "drive_time_urishall", "drive_time_agriculturequad", "drive_time_artsquad", "drive_time_engineeringquad",
            "nearest_stop_name", "walk_time_to_nearest_stop",
            "transit_time_to_ag_quad", "transit_time_to_arts_quad", "transit_time_to_eng_quad",
            "iso15"
        ]

        for col in calc_fields:
            src = f"{col}_existing"
            if src in existing_listings.columns:
                existing_listings[col] = existing_listings[src].fillna(existing_listings[col])
                existing_listings.drop(columns=[src], inplace=True, errors="ignore")

        existing_listings.drop(columns=["listingid"], inplace=True, errors="ignore")

    # ============================================================
    # 8) RECOMBINE DATA
    # ============================================================
    apartments_for_rent = pd.concat([new_listings, existing_listings], ignore_index=True)

    # ============================================================
    # 9) CALCULATE GLOBAL AMENITY + RENTAL FEATURES
    # ============================================================
    print("🏬 Calculating amenity scores...")
    apartments_for_rent = calculate_amenity_score.calculate_amenity_score(apartments_for_rent)

    print("📄 Extracting rental features...")
    apartments_for_rent = extract_rental_data.extract_rental_data(apartments_for_rent)
    apartments_for_rent = data_preprocessing.calc_adjusted_bed_bath_values(apartments_for_rent)

    print(f"📊 Listings ready for ML: {len(apartments_for_rent)}")

    # ============================================================
    # 10) ML PREPROCESSING + TRAINING
    # ============================================================
    print("🧹 Cleaning ML variables...")
    X, y = model_training.define_X_Y_variables(apartments_for_rent)
    X, y = data_preprocessing.clean_up_x_y(X, y)
    X = data_preprocessing.median_mode_imputation(X)
    y = data_preprocessing.log_transform_prices(y)

    X = X.reset_index(drop=True)
    apartments_for_rent = apartments_for_rent.reset_index(drop=True)
    y = y.reset_index(drop=True) if hasattr(y, 'reset_index') else pd.Series(y).reset_index(drop=True)
    
    X_with_coords = X.copy()
    if 'latitude' in apartments_for_rent.columns and 'longitude' in apartments_for_rent.columns:
        X_with_coords['latitude'] = apartments_for_rent['latitude'].values
        X_with_coords['longitude'] = apartments_for_rent['longitude'].values
    else:
        raise ValueError("Dataframe must contain 'latitude' and 'longitude' columns for spatial operations")

    print("🗺️ Adding H3 geospatial cells...")
    X_with_coords = model_training.add_h3_cells(X_with_coords, h3_reses=(6, 7))
    
    print("🗺️ Applying spatial spectral clustering...")
    X_with_coords = model_training.spatial_spectral_clustering(X_with_coords)
    
    x_cols = [col for col in X_with_coords.columns 
              if col not in ['spatial_cluster', 'latitude', 'longitude']]
    
    print("🤖 Running spatial block cross-validation...")
    metrics_df, avg = model_training.spatial_block_cv_xgb(
        X_with_coords, y, x_cols, 
        n_estimators=100, max_depth=6
    )
    
    print(f"📊 Spatial CV Results - Mean RMSE: {avg['rmse']:.4f}, Mean R²: {avg['r2']:.4f}")
    
    apartments_for_rent['spatial_cluster'] = X_with_coords['spatial_cluster'].values
    for res in (6, 7):
        h3_col = f"h3_{res}"
        if h3_col in X_with_coords.columns:
            apartments_for_rent[h3_col] = X_with_coords[h3_col].values
    
    print("💰 Computing fair rent predictions...")
    apartments_for_rent = model_training.compute_fair_rent(
        apartments_for_rent=apartments_for_rent,
        y=y,
        x_cols=x_cols,
        h3_reses=(6, 7),
        k_knn=10,
        n_estimators=100,
        max_depth=6
    )
    
    results_df = pd.DataFrame({
        'R2': [avg['r2']],
        'RMSE': [avg['rmse']],
        'MAE': [avg['mae']],
        'MAPE': [None], 
        'flagged': [False]
    }, index=['Spatial Block CV XGBoost'])
    
    X_spatial = X_with_coords
    y_clean = y
    best_model = 'Spatial Block CV XGBoost'

    # ============================================================
    # 11) CMA
    # ============================================================
    print("📈 Running CMA...")
    if 'predictedrent' not in apartments_for_rent.columns:
        apartments_for_rent['predictedrent'] = apartments_for_rent['PredictedRent']
    
    X_cma = comparative_market_analysis.define_X_for_cma(apartments_for_rent)
    apartments_for_rent = comparative_market_analysis.perform_cma(X_cma, apartments_for_rent)

    # ============================================================
    # 12) INSERT INTO DB
    # ============================================================
    print("💾 Inserting into database...")
    insert_into_postgredb.psql_insert_copy(apartments_for_rent)
    insert_into_postgredb.confirmation()

    # ============================================================
    # 13) PIPELINE METRICS
    # ============================================================
    print("📊 Generating pipeline metrics...")
    try:
        metrics = pipeline_metrics.analyze_market_and_model(apartments_for_rent, results_df, X, X_spatial, y_clean, best_model)
        pipeline_metrics.insert_pipeline_metrics(metrics)
    except Exception as e:
        print(f"⚠️ Error generating pipeline metrics: {e}")
        import traceback
        traceback.print_exc()

    print("✅ Pipeline complete!")
