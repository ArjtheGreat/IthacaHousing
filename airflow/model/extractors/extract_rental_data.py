import os
import json
import pandas as pd
import numpy as np
from shapely.geometry import Point
import geopandas as gpd
from pathlib import Path
from extractors.rent_basis_openai import classify_rent_bases
from extractors.rent_iqr_audit import (
    audit_normalized_rents, check_quote_amounts
)


def get_existing_rental_data():
    """
    Get existing rental extraction data from database
    """
    import os
    from sqlalchemy import create_engine, text
    
    DB_URI = os.getenv("DB_URI")
    if not DB_URI:
        return {}
    
    engine = create_engine(DB_URI)
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT listingid, shortdescription, available_bedrooms, available_bathrooms, 
                       rent_per_person, num_people, total_rent_amount
                FROM housing_listings 
                WHERE available_bedrooms IS NOT NULL
            """))
            
            existing_data = {}
            for row in result:
                listing_id = row[0]
                existing_data[listing_id] = {
                    'shortdescription': row[1],
                    'available_bedrooms': row[2],
                    'available_bathrooms': row[3],
                    'rent_per_person': row[4],
                    'num_people': row[5],
                    'total_rent_amount': row[6]
                }
            
            print(f"📊 Loaded {len(existing_data)} existing rental extractions")
            return existing_data
    except Exception as e:
        print(f"⚠️ Error fetching existing rental data: {e}")
        return {}

def deterministic_extract(row):
    """Normalize current structured rents without guessing a missing unit size.

    Unit-priced listings need a reliable bedroom count to determine per-person
    rent. A room/per-person price is already normalized. The raw unit rent is
    always preserved as total_rent_amount for Price Per Unit listings.
    """
    rent = pd.to_numeric(row.get("RentAmount"), errors="coerce")
    bedrooms = pd.to_numeric(row.get("Bedrooms"), errors="coerce")
    bathrooms = pd.to_numeric(row.get("Bathrooms"), errors="coerce")

    # Studio apartments have one rentable sleeping space for rent normalization.
    if pd.notna(bedrooms) and bedrooms == 0:
        bedrooms = 1.0
    if pd.notna(bedrooms) and bedrooms < 0:
        bedrooms = np.nan
    if pd.notna(bathrooms) and bathrooms <= 0:
        bathrooms = np.nan

    rent_type = str(row.get("RentType") or "")
    per_person = "person" in rent_type.lower()
    occupant_count = float(bedrooms) if pd.notna(bedrooms) else np.nan

    if pd.isna(rent) or rent <= 0:
        per_person_rent = np.nan
        total_rent = np.nan
    elif per_person:
        per_person_rent = float(rent)
        total_rent = float(rent) * occupant_count if pd.notna(occupant_count) else np.nan
    else:
        per_person_rent = float(rent) / occupant_count if pd.notna(occupant_count) and occupant_count > 0 else np.nan
        total_rent = float(rent)

    return {
        "available_bedrooms": occupant_count,
        "available_bathrooms": float(bathrooms) if pd.notna(bathrooms) else np.nan,
        "rent_per_person": per_person_rent,
        "num_people": occupant_count,
        "total_rent_amount": total_rent,
    }


def extract_rental_data(apartments_for_rent):
    """Recompute rents from the current floor-plan data on every pipeline run.

    Prior DB extraction caches were keyed by listing ID and description only,
    so rent/bed changes could incorrectly reuse old rent_per_person values.
    Structured fields are cheap to normalize; caching is unnecessary.
    Unknown per-unit bedroom counts remain missing instead of becoming 1.
    """
    out = apartments_for_rent.copy().reset_index(drop=True)
    extracted = pd.DataFrame(
        [deterministic_extract(row) for _, row in out.iterrows()],
        index=out.index,
    )
    for col in extracted.columns:
        out[col] = extracted[col]
    # The original source label is a fallback only: Cornell property-wide
    # "Price Per Unit" is often wrong for individual room/bedroom offerings.
    # Do not automatically flip cheap units based on IQR or model residuals.
    out["rent_per_person_original"] = out["rent_per_person"].copy()
    out["ithaca_insights_adjustment"] = False
    out["suspected_landlord_pricing_error"] = False
    out["pricing_adjustment_reason"] = None

    # First extract the advertised price basis from listing details only.
    out = classify_rent_bases(out)
    # A model can quote "$925 per bedroom" for a $1,850 whole-unit ad.
    # Such evidence describes the per-person SHARE, not the raw price basis:
    # refuse to flip the underlying amount, and flag the contradiction.
    out["rent_quote_amount_conflict"] = check_quote_amounts(out)
    explicit = (
        out["rent_basis_confidence"].eq("high")
        & out["rent_basis_evidence_type"].eq("explicit")
        & ~out["rent_quote_amount_conflict"]
    )
    # Only act on evidence-backed overrides. A model saying "this seems
    # cheap" is NOT sufficient to change the target labels.
    current_type = out["RentType"].fillna("").astype(str).str.casefold()
    new_person = explicit & out["rent_basis"].eq("per_person")
    new_unit = explicit & out["rent_basis"].eq("per_unit")
    to_person = new_person & ~current_type.str.contains("person")
    to_unit = new_unit & current_type.str.contains("person")

    advertised = pd.to_numeric(out["RentAmount"], errors="coerce")
    occupants = pd.to_numeric(out["num_people"], errors="coerce")
    valid = advertised.gt(0) & occupants.gt(0)
    to_person &= valid
    to_unit &= valid

    out.loc[to_person, "rent_per_person"] = advertised[to_person].astype(float)
    out.loc[to_person, "total_rent_amount"] = (
        advertised[to_person] * occupants[to_person]
    ).astype(float)
    out.loc[to_unit, "rent_per_person"] = (
        advertised[to_unit] / occupants[to_unit]
    ).astype(float)
    out.loc[to_unit, "total_rent_amount"] = advertised[to_unit].astype(float)

    adjusted = to_person | to_unit
    out.loc[adjusted, "ithaca_insights_adjustment"] = True
    out.loc[adjusted, "suspected_landlord_pricing_error"] = True
    out.loc[to_person, "pricing_adjustment_reason"] = "openai_source_verified_per_person"
    out.loc[to_unit, "pricing_adjustment_reason"] = "openai_source_verified_per_unit"
    print(
        f"🤖 Rent-basis source-evidenced overrides: {int(to_person.sum())} "
        f"unit→person, {int(to_unit.sum())} person→unit; "
        f"{int(out['rent_basis'].eq('unknown').sum())} ambiguous"
    )

    # Bedroom-specific 1.5x log-IQR compares both pricing interpretations.
    # A unique in-fence candidate can replace an unverified fallback;
    # verified source quotations still have priority.
    out = audit_normalized_rents(out)

    # Include adjusted amounts in the per-listing extraction payload.
    out["extracted_rental_data"] = out[[
        "available_bedrooms", "available_bathrooms", "rent_per_person",
        "num_people", "total_rent_amount",
    ]].to_dict(orient="records")
    unresolved = int(out["rent_per_person"].isna().sum())
    print(f"✅ Rent normalization: {len(out) - unresolved} priced, {unresolved} unresolved (excluded from rent model)")
    return out


MODEL_PATH = "/opt/airflow/model"
if not os.path.exists(MODEL_PATH):
    MODEL_PATH = str(Path(__file__).resolve().parent)

geojson_path = os.path.join(MODEL_PATH, "data", "IthacaN_Cleaned.geojson")

def extract_neighborhood(apartments_for_rent):
    """
    Extracts Neighborhood using Spatial Join
    """
    try:
        ithaca_neighborhoods_gdf = gpd.read_file(geojson_path)
    except FileNotFoundError:
        print("⚠️ IthacaN_Cleaned.geojson not found, skipping neighborhood extraction")
        return apartments_for_rent

    apartments_for_rent["Coordinates"] = apartments_for_rent.apply(
        lambda row: f'{{"lng": {row["longitude"]}, "lat": {row["latitude"]}}}'
        if pd.notna(row["longitude"]) and pd.notna(row["latitude"]) else None,
        axis=1
    )

    def parse_coordinates(x):
        if isinstance(x, str):
            try:
                coord_dict = json.loads(x)
                return Point(coord_dict["lng"], coord_dict["lat"])
            except (json.JSONDecodeError, KeyError, TypeError):
                return None
        elif isinstance(x, dict):
            return Point(x["lng"], x["lat"])
        else:
            return None
    
    apartments_for_rent["geometry"] = apartments_for_rent["Coordinates"].apply(parse_coordinates)

    apartments_for_rent_gdf = gpd.GeoDataFrame(
        apartments_for_rent, geometry="geometry", crs="EPSG:4326"
    )
    
    # Drop index columns from previous spatial joins to avoid conflicts
    index_cols_to_drop = ['index_right', 'index_left']
    existing_index_cols = [col for col in index_cols_to_drop if col in apartments_for_rent_gdf.columns]
    if existing_index_cols:
        apartments_for_rent_gdf = apartments_for_rent_gdf.drop(columns=existing_index_cols)
    
    result_gdf = apartments_for_rent_gdf.sjoin(ithaca_neighborhoods_gdf, how='left')
    result_gdf = result_gdf.rename(columns={'name': 'neighborhood'})
    
    if 'neighborhood' in result_gdf.columns:
        non_null_neighborhoods = result_gdf['neighborhood'].notna().sum()
        print(f"✅ Neighborhood extraction: {non_null_neighborhoods}/{len(result_gdf)} listings have neighborhoods")
        if non_null_neighborhoods > 0:
            print(f"📊 Sample neighborhoods: {result_gdf['neighborhood'].value_counts().head(5).to_dict()}")
    else:
        print("⚠️ WARNING: 'neighborhood' column not found after spatial join!")
        print(f"📋 Available columns: {list(result_gdf.columns)}")
    
    result_df = result_gdf.drop(columns=['geometry'])

    return result_df