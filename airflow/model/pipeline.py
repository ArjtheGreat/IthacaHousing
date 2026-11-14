import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path

MODEL_PATH = "/opt/airflow/model"
if not os.path.exists(MODEL_PATH):
    MODEL_PATH = os.path.dirname(os.path.abspath(__file__))
if MODEL_PATH not in sys.path:
    sys.path.insert(0, MODEL_PATH)

import core.fetch_housing_data as fetch_housing_data
import core.excluded_listing_unit_ids as excluded_listing_unit_ids
import core.amenity_overrides as amenity_overrides
import core.insert_into_postgredb as insert_into_postgredb
import core.pipeline_metrics as pipeline_metrics
import core.property_level as property_level

import calculators.calculate_amenity_score as calculate_amenity_score
import calculators.calculate_travel_times_distance as calculate_travel_times_distance
import calculators.calculate_transit_score as calculate_transit_score

import extractors.extract_safety_features as extract_safety_features
import extractors.extract_rental_data as extract_rental_data
import extractors.assign_wards as assign_wards
import extractors.assign_bid as assign_bid
import extractors.enrich_tompkins_parcels as enrich_tompkins_parcels
import extractors.shared_facilities_openai as shared_facilities_openai
import extractors.extract_land_assessment_features as extract_land_assessment_features
import extractors.extract_poi_features as extract_poi_features
import core.landlord_extraction as landlord_extraction

import ml.data_preprocessing as data_preprocessing
import ml.model_training as model_training
import ml.comparative_market_analysis as comparative_market_analysis
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
            existing_ids = {str(row[0]) for row in result if row[0] is not None}
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
            # Optional county fields may not exist before the first GIS ingest.
            # Select them dynamically so old databases still load cleanly.
            present = {
                row[0] for row in conn.execute(text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema = 'public' AND table_name = 'housing_listings'"
                ))
            }
            parcel_optional = [
                "year_built_source", "parcel_printkey", "parcel_match_method",
                "assessment_total_value", "assessment_land_value",
                "assessment_stories", "assessment_zoning",
                "assessment_property_class",
            ]
            extra = ", " + ", ".join(
                col for col in parcel_optional if col in present
            ) if any(col in present for col in parcel_optional) else ""
            query = text(f"""
                SELECT listingid, listingaddress, listingcity, listingzip, neighborhood,
                       rentamount, rent_per_person, available_bedrooms, available_bathrooms,
                       year_built, createdate, listingexpirationdate, lengthavailable,
                       housingtype, owner_name, listingtypes, sale_price, property_acres,
                       assessment_sqft, neighborhood_assessment, property_depth,
                       property_frontage, property_pc, water_access, sewer_access,
                       sewer_name, latitude, longitude, drive_time_urishall,
                       drive_time_agriculturequad, drive_time_artsquad, drive_time_engineeringquad{extra}
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

def get_manual_rent_overrides():
    """Read human-corrected rents before retraining. Fail closed if DB is unavailable.

    Only rent_per_person is manually protected; all other source attributes
    are refreshed normally. A separate review workflow remains authoritative
    for source price/basis classification.
    """
    if engine is None:
        raise RuntimeError("DB_URI is required to preserve manual rent corrections")
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT listingid, rent_per_person
            FROM public.housing_listings
            WHERE rent_manual_override IS TRUE
        """)).mappings().all()

    overrides = {}
    for row in rows:
        rent = pd.to_numeric(row["rent_per_person"], errors="coerce")
        if not np.isfinite(rent) or rent <= 0:
            raise ValueError(
                f"Invalid protected rent for listing {row['listingid']!r}: {row['rent_per_person']!r}"
            )
        overrides[str(row["listingid"])] = float(rent)
    return overrides


def apply_manual_rent_overrides(listings):
    """Apply protected rents after rent extraction but before filtering and ML."""
    overrides = get_manual_rent_overrides()
    listings = listings.copy()
    ids = listings["ListingId"].astype(str)
    listings["rent_manual_override"] = ids.isin(overrides)
    protected = listings["rent_manual_override"]
    if protected.any():
        listings.loc[protected, "rent_per_person"] = ids.loc[protected].map(overrides).to_numpy()
    print(f"🔒 Preserved {int(protected.sum())} manual rent corrections")
    return listings


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
            
            poi_columns = [
                f"{kind}_{suffix}"
                for kind in ("food", "attractions", "shopping", "grocery")
                for suffix in ("count_200m", "nearest_dist")
            ]
            columns_to_select = [col for col in base_columns + new_travel_columns + transit_columns + poi_columns if col in existing_columns]
            if "iso15" in existing_columns and "iso15" not in columns_to_select:
                columns_to_select.append("iso15")
            
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



def apply_manual_rent_overrides(listings):
    """Preserve explicitly flagged per-person rents from the live database.

    This runs after rent extraction and before ML/CMA. A database/read error
    must abort the refresh rather than silently erase existing manual edits.
    The scraper's computed value remains in rent_per_person_original.
    """
    if engine is None:
        raise RuntimeError("DB_URI must be configured to preserve manual rent overrides")
    if "ListingId" not in listings or "rent_per_person" not in listings:
        raise ValueError("ListingId and rent_per_person are required for overrides")

    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT listingid, rent_per_person
            FROM housing_listings
            WHERE rent_manual_override IS TRUE
        """)).fetchall()

    overrides = {}
    for listing_id, rent in rows:
        number = pd.to_numeric(rent, errors="coerce")
        if pd.isna(number) or not np.isfinite(number) or number <= 0:
            raise ValueError(f"Invalid manually overridden rent for listing {listing_id}")
        overrides[str(listing_id)] = float(number)

    out = listings.copy()
    ids = out["ListingId"].astype("string")
    matched = ids.isin(overrides)
    out["rent_manual_override"] = matched.fillna(False).astype(bool)

    if matched.any():
        out.loc[matched, "rent_per_person"] = (
            ids.loc[matched].map(overrides).astype(float).to_numpy()
        )

    unmatched_count = len(set(overrides) - set(ids.dropna().astype(str)))
    print(
        f"✏️ Preserved {int(matched.sum())} listing rows with manual rent overrides; "
        f"{unmatched_count} flagged listings no longer present in the scrape"
    )
    return out


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
    existing_df["listingid"] = existing_df["listingid"].astype(str)
    existing_df = existing_df[existing_df["listingid"].notna() & (existing_df["listingid"] != "nan")].copy()

    new_ids_str = {str(x) for x in new_ids if x is not None and str(x) not in ("", "nan", "None")}
    removed_df = existing_df[~existing_df["listingid"].isin(new_ids_str)].copy()

    if removed_df.empty:
        print("✅ No removed listings detected this run")
        return

    print(f"🗑️ Detected {len(removed_df)} removed listings - recording...")

    records = []
    for _, row in removed_df.iterrows():
        record = {
            'listingid': str(row['listingid']) if pd.notna(row['listingid']) else None,
            'listingaddress': str(row.get('listingaddress', '')) if pd.notna(row.get('listingaddress')) else None,
            'listingcity': str(row.get('listingcity', '')) if pd.notna(row.get('listingcity')) else None,
            'listingzip': str(row.get('listingzip', '')) if pd.notna(row.get('listingzip')) else None,
            'neighborhood': str(row.get('neighborhood', '')) if pd.notna(row.get('neighborhood')) else None,
            'rentamount': float(row.get('rentamount', 0)) if pd.notna(row.get('rentamount')) else None,
            'rent_per_person': int(row.get('rent_per_person', 0)) if pd.notna(row.get('rent_per_person')) else 0,
            'available_bedrooms': int(row.get('available_bedrooms', 0)) if pd.notna(row.get('available_bedrooms')) else 0,
            'available_bathrooms': int(row.get('available_bathrooms', 0)) if pd.notna(row.get('available_bathrooms')) else 0,
            'year_built': int(row.get('year_built', 0)) if pd.notna(row.get('year_built')) and row.get('year_built', 0) > 0 else None,
            'sale_price': float(row.get('sale_price', 0)) if pd.notna(row.get('sale_price')) and row.get('sale_price', 0) > 0 else None,
            'property_acres': float(row.get('property_acres', 0)) if pd.notna(row.get('property_acres')) and row.get('property_acres', 0) > 0 else None,
            'assessment_sqft': float(row.get('assessment_sqft', 0)) if pd.notna(row.get('assessment_sqft')) and row.get('assessment_sqft', 0) > 0 else None,
            'latitude': float(row.get('latitude', 0)) if pd.notna(row.get('latitude')) else None,
            'longitude': float(row.get('longitude', 0)) if pd.notna(row.get('longitude')) else None,
            'drive_time_urishall': float(row.get('drive_time_urishall', 0)) if pd.notna(row.get('drive_time_urishall')) else None,
            'drive_time_agriculturequad': float(row.get('drive_time_agriculturequad', 0)) if pd.notna(row.get('drive_time_agriculturequad')) else None,
            'drive_time_artsquad': float(row.get('drive_time_artsquad', 0)) if pd.notna(row.get('drive_time_artsquad')) else None,
            'drive_time_engineeringquad': float(row.get('drive_time_engineeringquad', 0)) if pd.notna(row.get('drive_time_engineeringquad')) else None,
            'createdate': pd.to_datetime(row.get('createdate')).to_pydatetime() if pd.notna(row.get('createdate')) else None,
            'listingexpirationdate': pd.to_datetime(row.get('listingexpirationdate')).to_pydatetime() if pd.notna(row.get('listingexpirationdate')) else None,
            'lengthavailable': float(row.get('lengthavailable', 0)) if pd.notna(row.get('lengthavailable')) else None,
            'housingtype': str(row.get('housingtype', '')) if pd.notna(row.get('housingtype')) else None,
            'owner_name': str(row.get('owner_name', '')) if pd.notna(row.get('owner_name')) else '',
            'listingtypes': str(row.get('listingtypes', '')) if pd.notna(row.get('listingtypes')) else None,
        }
        records.append(record)

    try:
        with engine.begin() as conn:
            insert_sql = text("""
                INSERT INTO sold_listings (
                    listingid, listingaddress, listingcity, listingzip, neighborhood,
                    rentamount, rent_per_person, available_bedrooms, available_bathrooms,
                    year_built, sale_price, property_acres, assessment_sqft, latitude, longitude,
                    drive_time_urishall, drive_time_agriculturequad, drive_time_artsquad, drive_time_engineeringquad,
                    createdate, listingexpirationdate, lengthavailable, housingtype, owner_name, listingtypes,
                    removed_timestamp
                )
                VALUES (
                    :listingid, :listingaddress, :listingcity, :listingzip, :neighborhood,
                    :rentamount, :rent_per_person, :available_bedrooms, :available_bathrooms,
                    :year_built, :sale_price, :property_acres, :assessment_sqft, :latitude, :longitude,
                    :drive_time_urishall, :drive_time_agriculturequad, :drive_time_artsquad, :drive_time_engineeringquad,
                    :createdate, :listingexpirationdate, :lengthavailable, :housingtype, :owner_name, :listingtypes,
                    CURRENT_DATE
                )
                ON CONFLICT (listingid)
                DO UPDATE SET removed_timestamp = EXCLUDED.removed_timestamp;
            """)

            conn.execute(insert_sql, records)

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

    # Cornell reports square footage for individual floorplans, not parcels.
    # Keep it numeric and missing when unavailable, so XGBoost can handle
    # missing areas without ever replacing them with assessment_sqft.
    if "unit_sqft" not in apartments_for_rent.columns and "SqFt" in apartments_for_rent.columns:
        apartments_for_rent["unit_sqft"] = apartments_for_rent["SqFt"]
    if "unit_sqft" not in apartments_for_rent.columns:
        apartments_for_rent["unit_sqft"] = np.nan
    area = pd.to_numeric(apartments_for_rent["unit_sqft"], errors="coerce")
    apartments_for_rent["unit_sqft"] = area.where(area > 0)
    available_areas = int(apartments_for_rent["unit_sqft"].notna().sum())
    print(
        f"📐 Cornell unit_sqft available for {available_areas}/"
        f"{len(apartments_for_rent)} floorplans"
    )
    if available_areas == 0:
        print("⚠️ No floorplan areas received; XGBoost cannot learn a SQFT effect on this run")

    apartments_for_rent = property_level.ensure_property_id(apartments_for_rent)
    apartments_for_rent = amenity_overrides.normalize_known_addresses(apartments_for_rent)

    # Load preserved enrichment BEFORE re-running owner, parcel and
    # neighborhood lookups. These values will be replaced by the latest
    # source listing contact fields, which are fetched fresh above.
    existing_listings_df = get_existing_listings_dataframe()
    existing_calculated = get_existing_calculated_data()

    print("🛡️ Adding safety features (once per PropertyId)...")
    apartments_for_rent = property_level.apply_per_property(
        apartments_for_rent,
        extract_safety_features.calculate_safety_score,
        label="safety",
    )

    print("👤 Extracting landlord + property info...")
    apartments_for_rent = property_level.apply_cached_property_enrichment(
        apartments_for_rent, existing_listings_df,
        landlord_extraction.extract_landlord_names,
        fields=["owner_name"], required=["owner_name"], label="owner names",
    )
    parcel_fields = [
        "neighborhood_assessment", "property_depth", "property_frontage",
        "property_acres", "property_pc", "water_access", "sewer_access",
        "sewer_name", "year_built", "sale_price", "assessment_sqft",
        "year_built_source", "parcel_printkey", "parcel_match_method",
        "assessment_total_value", "assessment_land_value",
        "assessment_stories", "assessment_zoning", "assessment_property_class",
    ]
    # Cache parcel lookup only where a substantive value was previously saved.
    parcel_cache = existing_listings_df.copy()
    if not parcel_cache.empty:
        have_parcel = parcel_cache[
            [c for c in parcel_fields if c in parcel_cache.columns]
        ].notna().any(axis=1)
        parcel_cache = parcel_cache.loc[have_parcel].copy()
        parcel_cache["_parcel_cached"] = True
    # Use an explicit cache marker so rows with legitimate NULL parcel
    # attributes can still be reused if at least one detail was matched.
    apartments_for_rent = property_level.apply_cached_property_enrichment(
        apartments_for_rent, parcel_cache,
        landlord_extraction.add_property_details,
        fields=parcel_fields + ["_parcel_cached"],
        required=["_parcel_cached"], label="parcel details",
    )
    apartments_for_rent = apartments_for_rent.drop(columns=["_parcel_cached"], errors="ignore")

    # Recompute after updating boundary files; the prior DB cache contains
    # outdated seven-neighborhood labels and must not mask the new 19 names.
    # County GIS is a fresh, geometry-based second source. Fill gaps in the
    # legacy ownership/assessment CSV without overwriting known years or
    # treating parcel SQ_FT as unit floorplan area.
    print("🏗️ Filling missing parcel assessments from 2026 Tompkins County GIS...")
    year_before = int(pd.to_numeric(
        apartments_for_rent.get("year_built"), errors="coerce"
    ).notna().sum()) if "year_built" in apartments_for_rent else 0
    try:
        apartments_for_rent = property_level.apply_per_property(
            apartments_for_rent,
            enrich_tompkins_parcels.enrich_from_2026_parcels,
            label="county parcel GIS",
        )
        year_after = pd.to_numeric(apartments_for_rent["year_built"], errors="coerce").notna().sum()
        print(f"📊 Construction years: {year_before} before county GIS, "
              f"{year_after} after (+{year_after - year_before} rows)")
    except (OSError, RuntimeError, ValueError, KeyError) as exc:
        # The county endpoint can occasionally be unavailable. Existing
        # CSV-derived fields remain intact and the full ingest may proceed.
        print(f"⚠️ Parcel GIS enrichment unavailable; keeping legacy values: {exc}")
        # Previously a failed GIS query was easy to miss, leaving all new
        # assessment columns NULL without a useful Airflow traceback.
        import traceback
        traceback.print_exc()
        if os.getenv("TOMPKINS_PARCEL_REQUIRED", "0") == "1":
            raise


    print("📍 Extracting 2010 neighborhoods (once per PropertyId)...")
    apartments_for_rent = property_level.apply_per_property(
        apartments_for_rent,
        extract_rental_data.extract_neighborhood,
        label="2010 neighborhoods",
    )

    # Ward is distinct from the existing neighborhood field and should be
    # computed from current coordinates, not reused across boundary changes.
    print("🏛️ Assigning 2022 Ithaca wards (once per property)...")
    apartments_for_rent = property_level.apply_per_property(
        apartments_for_rent, assign_wards.assign_wards, label="city wards",
    )

    print("🏙️ Assigning official Ithaca Business Improvement District flag...")
    apartments_for_rent = property_level.apply_per_property(
        apartments_for_rent, assign_bid.assign_bid, label="business improvement district",
    )

    print("🏗️ Adding property/structural features...")
    apartments_for_rent = data_preprocessing.add_property_features(apartments_for_rent)

    print("🏛️ Extracting land assessment features...")
    apartments_for_rent = extract_land_assessment_features.extract_land_assessment_features(apartments_for_rent)

    print("📍 Extracting POI features (once per PropertyId)...")
    poi_fields = [
        f"{kind}_{suffix}"
        for kind in ("food", "attractions", "shopping", "grocery")
        for suffix in ("count_200m", "nearest_dist")
    ]
    apartments_for_rent = property_level.apply_cached_property_enrichment(
        apartments_for_rent, existing_calculated,
        extract_poi_features.extract_poi_features,
        fields=poi_fields,
        required=[f"{kind}_count_200m" for kind in
                  ("food", "attractions", "shopping", "grocery")],
        label="poi",
    )

    # ============================================================
    # 3) FETCH EXISTING DATA FROM DB
    # ============================================================
    # Previously persisted values were loaded before enrichment.

    # ============================================================
    # 4) TRACK REMOVED LISTINGS (still by ListingId / unit)
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
    # 5) TRAVEL / TRANSIT / ISO — once per PropertyId
    # ============================================================
    calc_fields = [
        "transit_score", "amenities_score", "valid_certificate_of_compliance",
        "nearest_neighbor_listingids",
        "walk_time_urishall", "walk_time_agriculturequad", "walk_time_artsquad", "walk_time_engineeringquad",
        "bike_time_urishall", "bike_time_agriculturequad", "bike_time_artsquad", "bike_time_engineeringquad",
        "drive_time_urishall", "drive_time_agriculturequad", "drive_time_artsquad", "drive_time_engineeringquad",
        "nearest_stop_name", "walk_time_to_nearest_stop",
        "transit_time_to_ag_quad", "transit_time_to_arts_quad", "transit_time_to_eng_quad",
        "iso15",
    ]

    existing_by_prop = pd.DataFrame()
    if isinstance(existing_calculated, pd.DataFrame) and not existing_calculated.empty:
        existing_by_prop = existing_calculated.copy()
        existing_by_prop["PropertyId"] = property_level.property_id_from_listing_id(
            existing_by_prop["listingid"]
        )
        score_col = "transit_score" if "transit_score" in existing_by_prop.columns else None
        if score_col:
            existing_by_prop["_filled"] = existing_by_prop[score_col].notna().astype(int)
            existing_by_prop = existing_by_prop.sort_values("_filled", ascending=False)
        existing_by_prop = existing_by_prop.drop_duplicates(subset=["PropertyId"], keep="first")
        if "_filled" in existing_by_prop.columns:
            existing_by_prop = existing_by_prop.drop(columns=["_filled"])

    known_props = set(existing_by_prop["PropertyId"].astype(str)) if not existing_by_prop.empty else set()
    apartments_for_rent = property_level.ensure_property_id(apartments_for_rent)
    all_props = set(apartments_for_rent["PropertyId"].astype(str))
    props_needing = all_props - known_props

    print(
        f"🗺️ Spatial calc: {len(props_needing)} new properties, "
        f"{len(known_props & all_props)} reused from DB "
        f"(of {len(all_props)} total)"
    )

    need_mask = apartments_for_rent["PropertyId"].isin(props_needing)
    need_df = apartments_for_rent.loc[need_mask].copy()
    have_df = apartments_for_rent.loc[~need_mask].copy()

    if len(need_df) > 0:
        print("🗺️ Calculating travel/transit/iso (new properties only)...")
        graphs = calculate_travel_times_distance.build_graphs()

        def _travel_transit_iso(reps):
            reps = calculate_travel_times_distance.compute_all_travel_times(reps, graphs)
            reps = calculate_travel_times_distance.make_isochronic_map(reps)
            reps = calculate_transit_score.calculate_transit_score(reps)
            return reps

        need_df = property_level.apply_per_property(
            need_df, _travel_transit_iso, label="travel/transit/iso"
        )

    if len(have_df) > 0 and not existing_by_prop.empty:
        print("🔄 Merging preserved calculations by PropertyId...")
        merge_cols = ["PropertyId"] + [
            c for c in calc_fields if c in existing_by_prop.columns
        ]
        have_df = have_df.drop(
            columns=[c for c in calc_fields if c in have_df.columns],
            errors="ignore",
        )
        have_df = have_df.merge(
            existing_by_prop[merge_cols],
            on="PropertyId",
            how="left",
        )

    apartments_for_rent = pd.concat([need_df, have_df], ignore_index=True)

    # ============================================================
    # 6) AMENITY + RENTAL FEATURES
    # ============================================================
    print("🏬 Calculating amenity scores (once per PropertyId)...")
    apartments_for_rent = property_level.apply_per_property(
        apartments_for_rent,
        calculate_amenity_score.calculate_amenity_score,
        label="amenities",
    )

    apartments_for_rent = calculate_amenity_score.add_canonical_amenities(apartments_for_rent)
    apartments_for_rent = amenity_overrides.apply_amenity_overrides(apartments_for_rent)

    # Apply explicit unit-level exclusions before ML and before any DB insert.
    # The atomic UPSERT + stale-ID reconciliation removes excluded units
    # from Supabase on a successful complete refresh.
    apartments_for_rent = excluded_listing_unit_ids.exclude_listing_units(
        apartments_for_rent
    )

    print("📄 Extracting rental features...")
    apartments_for_rent = extract_rental_data.extract_rental_data(apartments_for_rent)
    apartments_for_rent = data_preprocessing.calc_adjusted_bed_bath_values(apartments_for_rent)

    # Manual rent edits in Supabase win over freshly scraped/calculated rents.
    # Apply before rent validity filtering, CV training, and fair-value modeling.
    apartments_for_rent = apply_manual_rent_overrides(apartments_for_rent)
    # Keep manually verified per-person rents through the TRUNCATE + INSERT.
    # Apply before ML, CV, and CMA so all outputs use the corrected target.
    apartments_for_rent = apply_manual_rent_overrides(apartments_for_rent)

    # Preserve 0=studio in ML, separately from occupants used for rent math.
    apartments_for_rent["model_bedrooms"] = pd.to_numeric(
        apartments_for_rent["Bedrooms"], errors="coerce"
    ).clip(lower=0)
    apartments_for_rent = shared_facilities_openai.classify_shared_facilities(
        apartments_for_rent
    )
    apartments_for_rent["physical_bedrooms"] = apartments_for_rent["model_bedrooms"]

    # A listing without a valid rent per person is neither a training sample
    # nor a publishable housing listing. Never add it back before DB insertion.
    rent_values = pd.to_numeric(apartments_for_rent["rent_per_person"], errors="coerce")
    priced = rent_values.notna() & np.isfinite(rent_values) & rent_values.gt(0)
    excluded_unpriced = int((~priced).sum())
    apartments_for_rent = apartments_for_rent.loc[priced].copy().reset_index(drop=True)
    print(
        f"📊 Listings ready for ML and database: {len(apartments_for_rent)}; "
        f"{excluded_unpriced} unpriced listings excluded from both"
    )
    if apartments_for_rent.empty:
        raise ValueError("No listings with reliable per-person rents to train on")

    # ============================================================
    # 10) ML PREPROCESSING + TRAINING
    # ============================================================
    print("🧹 Preparing numerical rent-model predictors...")
    X, rent_dollars = model_training.define_X_Y_variables(apartments_for_rent)
    if "unit_sqft" not in X.columns:
        raise ValueError("unit_sqft was dropped before XGBoost training")
    print(
        f"📐 Training with unit_sqft: "
        f"{int(pd.to_numeric(X['unit_sqft'], errors='coerce').notna().sum())}/"
        f"{len(X)} listings have source floorplan area"
    )

    # No global median imputation before CV: avoid training data leakage.
    # XGBoost handles missing numerical values natively in each fold.
    X = X.apply(pd.to_numeric, errors="coerce").replace([float("inf"), float("-inf")], float("nan"))
    apartments_for_rent = apartments_for_rent.reset_index(drop=True)
    rent_dollars = pd.to_numeric(rent_dollars, errors="coerce").reset_index(drop=True)
    y = np.log(rent_dollars)
    for col in X.columns:
        apartments_for_rent[col] = X[col].reset_index(drop=True)

    if 'latitude' not in apartments_for_rent or 'longitude' not in apartments_for_rent:
        raise ValueError("Missing latitude/longitude for rent model")
    apartments_for_rent["latitude"] = pd.to_numeric(apartments_for_rent["latitude"], errors="coerce")
    apartments_for_rent["longitude"] = pd.to_numeric(apartments_for_rent["longitude"], errors="coerce")

    print("💰 Training one XGBoost per landlord-held-out fold...")
    apartments_for_rent, fold_metrics, overall, feature_importance = (
        model_training.compute_fair_rent_oof(
            apartments_for_rent=apartments_for_rent,
            y=y,
            x_cols=list(X.columns),
            n_splits=5,
            n_estimators=100,
            max_depth=6,
            group_level="landlord",
        )
    )
    print("\n📊 OOF fold metrics ($ per person per month):")
    print(fold_metrics.to_string(index=False, float_format=lambda v: f"{v:,.2f}"))
    print("\n📊 Pooled held-out-landlord metrics:")
    for key in ("r2", "rmse", "mae", "bias", "median_residual", "residual_std", "p90_abs_error"):
        print(f"  {key}: {overall[key]:,.3f}")
    print("\n⭐ Most important rent predictors:")
    print(feature_importance.head(15).to_string(index=False))

    # Metrics now describe the very same OOF predictions shown on the site.
    results_df = pd.DataFrame({
        "R2": [overall["r2"]],
        "RMSE": [overall["rmse"]],
        "MAE": [overall["mae"]],
        "MAPE": [None],
        "flagged": [False],
    }, index=["Landlord-Grouped OOF XGBoost"])
    X_spatial = X.copy()
    y_clean = y
    best_model = "Landlord-Grouped OOF XGBoost"

    # ============================================================
    # 11) CMA
    # ============================================================
    print("📈 Running CMA...")
    if "predictedrent" not in apartments_for_rent.columns:
        if "PredictedRent" in apartments_for_rent.columns:
            apartments_for_rent["predictedrent"] = apartments_for_rent["PredictedRent"]
        elif "fair_rent" in apartments_for_rent.columns:
            apartments_for_rent["predictedrent"] = apartments_for_rent["fair_rent"]
            apartments_for_rent["PredictedRent"] = apartments_for_rent["fair_rent"]
    
    X_cma = comparative_market_analysis.define_X_for_cma(apartments_for_rent)
    apartments_for_rent = comparative_market_analysis.perform_cma(X_cma, apartments_for_rent)

    # ============================================================
    # 12) INSERT INTO DB
    # ============================================================
    # Store only listings with a valid positive rent/person in Supabase.
    # An independent guard in psql_insert_copy enforces this policy too.
    priced_listings_for_metrics = apartments_for_rent
    print("💾 Inserting priced listings into database...")
    insert_into_postgredb.psql_insert_copy(apartments_for_rent)
    insert_into_postgredb.confirmation()

    # ============================================================
    # 13) PIPELINE METRICS
    # ============================================================
    print("📊 Generating pipeline metrics...")
    try:
        metrics = pipeline_metrics.analyze_market_and_model(
            priced_listings_for_metrics, results_df, X, X_spatial,
            y_clean, best_model,
            oof_feature_importance=feature_importance,
            oof_fold_metrics=fold_metrics,
            oof_overall_metrics=overall,
        )
        pipeline_metrics.insert_pipeline_metrics(metrics)
    except Exception as e:
        print(f"⚠️ Error generating pipeline metrics: {e}")
        import traceback
        traceback.print_exc()

    print("✅ Pipeline complete!")
