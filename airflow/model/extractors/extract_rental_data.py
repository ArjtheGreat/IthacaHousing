import os
import json
import pandas as pd
import numpy as np
from shapely.geometry import Point
import geopandas as gpd
from pathlib import Path
from extractors.rent_iqr_audit import audit_normalized_rents
from sqlalchemy import create_engine, text


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

def load_rent_basis_reviews():
    """Read durable human/source-verified classifications before the refresh.

    Fail closed on an actual DB outage: losing reviewed corrections silently
    would corrupt the training targets on the next full-table replacement.
    """
    uri = os.getenv("DB_URI")
    if not uri:
        raise RuntimeError("DB_URI is required for persistent rent reviews")
    engine = create_engine(uri, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            rows = connection.execute(text("""
                SELECT listingid, source_rentamount, source_bedrooms,
                       confirmed_basis, review_status, evidence
                FROM public.rent_basis_reviews
                WHERE review_status IN ('confirmed','needs_review')
            """)).mappings().all()
            return {str(row["listingid"]): dict(row) for row in rows}
    finally:
        engine.dispose()


def deterministic_extract(row):
    """Normalize current structured rents without guessing a missing unit size.

    Unit-priced listings need a reliable bedroom count to determine per-person
    rent. A room/per-person price is already normalized. The raw unit rent is
    always preserved as total_rent_amount for Price Per Unit listings.
    """
    rent = pd.to_numeric(row.get("RentAmount"), errors="coerce")
    bedrooms = pd.to_numeric(row.get("Bedrooms"), errors="coerce")
    bathrooms = pd.to_numeric(row.get("Bathrooms"), errors="coerce")

    # A studio stays 0 bedrooms. Only the per-person division below treats 0 as 1.
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
        if pd.isna(occupant_count):
            per_person_rent = np.nan
        else:
            # Keep 0 bedrooms in the features; substitute 1 only for this division.
            divisor = occupant_count if occupant_count > 0 else 1.0
            per_person_rent = float(rent) / divisor
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

    # Persisted reviews survive the housing_listings TRUNCATE on every ingest.
    # Only source-price + bedroom-count matches qualify as confirmations.
    reviews = load_rent_basis_reviews()
    out["rent_basis"] = "unknown"
    out["rent_final_basis"] = "unknown"
    out["rent_basis_confidence"] = "low"
    out["rent_basis_evidence"] = ""
    out["rent_basis_evidence_type"] = "none"
    out["rent_basis_source"] = "iqr_only"
    out["rent_basis_evidence_field"] = "none"
    out["rent_basis_fingerprint"] = None
    out["rent_quote_amount_conflict"] = False
    out["rent_verification_status"] = "review"
    out["rent_basis_review_status"] = "unverified"

    raw = pd.to_numeric(out["RentAmount"], errors="coerce")
    bedrooms = pd.to_numeric(out["Bedrooms"], errors="coerce")
    for i, row in out.iterrows():
        review = reviews.get(str(row["ListingId"]))
        if not review:
            continue
        if pd.isna(raw[i]) or pd.isna(bedrooms[i]):
            continue
        if abs(float(raw[i]) - float(review["source_rentamount"])) > .51:
            continue
        if abs(float(bedrooms[i]) - float(review["source_bedrooms"])) > .01:
            continue

        if review["review_status"] == "needs_review":
            # Advertised "bedrooms" may be an entire complex rather than a unit.
            out.at[i, "rent_per_person"] = np.nan
            out.at[i, "total_rent_amount"] = np.nan
            out.at[i, "rent_basis_review_status"] = "needs_review"
            continue
        if review["review_status"] != "confirmed":
            continue
        basis = review["confirmed_basis"]
        if basis not in ("per_person", "per_unit") or bedrooms[i] < 0:
            continue
        divisor = float(bedrooms[i]) if bedrooms[i] > 0 else 1.0
        expected = (
            float(raw[i]) if basis == "per_person"
            else float(raw[i] / divisor)
        )
        out.at[i, "rent_per_person"] = expected
        out.at[i, "total_rent_amount"] = (
            float(raw[i] * bedrooms[i]) if basis == "per_person"
            else float(raw[i])
        )
        out.at[i, "rent_basis"] = basis
        out.at[i, "rent_final_basis"] = basis
        out.at[i, "rent_basis_confidence"] = "high"
        out.at[i, "rent_basis_evidence"] = review.get("evidence") or ""
        out.at[i, "rent_basis_evidence_type"] = "explicit"
        out.at[i, "rent_basis_source"] = "persistent_review"
        out.at[i, "rent_verification_status"] = "source_verified"
        out.at[i, "rent_basis_review_status"] = "confirmed"
        old = pd.to_numeric(out.at[i, "rent_per_person_original"], errors="coerce")
        if pd.isna(old) or abs(float(old) - expected) > .51:
            out.at[i, "ithaca_insights_adjustment"] = True
            out.at[i, "suspected_landlord_pricing_error"] = True
            out.at[i, "pricing_adjustment_reason"] = (
                "reviewed_source_verified_" + basis
            )

    # No model calls. Only a bedroom-specific IQR from reviewed reference rents.
    out = audit_normalized_rents(out)
    blocked = out["rent_basis_review_status"].eq("needs_review")
    out.loc[blocked, "rent_per_person"] = np.nan
    out.loc[blocked, "total_rent_amount"] = np.nan
    out.loc[blocked, "rent_final_basis"] = "unknown"
    out.loc[blocked, "rent_review_flag"] = True
    out.loc[blocked, "rent_review_reason"] = "bedrooms_may_be_building_total"
    out.loc[blocked, "rent_verification_status"] = "review"
    # Transient review status is not a persisted housing_listings column.
    out.drop(columns=["rent_basis_review_status"], inplace=True)

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

geojson_path = os.path.join(MODEL_PATH, "data", "neighborhoods.geojson")

def extract_neighborhood(apartments_for_rent):
    """Assign James Spokes' named Ithaca neighborhoods to each property/unit.

    Preserve exactly one result per input record on polygon overlaps and
    shared boundaries. Coordinates and polygons are WGS84.
    """
    neighborhoods = gpd.read_file(geojson_path)
    if "name" not in neighborhoods.columns:
        raise ValueError("Neighborhood GeoJSON needs a 'name' property")
    if neighborhoods.crs is None:
        raise ValueError("Neighborhood GeoJSON must declare a CRS")
    neighborhoods = neighborhoods.to_crs("EPSG:4326")
    neighborhoods = neighborhoods.loc[neighborhoods.geometry.notna()].copy()
    if neighborhoods.empty:
        raise ValueError("Neighborhood GeoJSON contains no polygons")

    out = apartments_for_rent.copy().reset_index(drop=True)
    out = out.drop(columns=["neighborhood", "index_right", "index_left"], errors="ignore")
    lat = pd.to_numeric(out["latitude"], errors="coerce")
    lon = pd.to_numeric(out["longitude"], errors="coerce")
    valid = lat.between(-90, 90) & lon.between(-180, 180)
    out["neighborhood"] = pd.Series(pd.NA, index=out.index, dtype="string")
    if valid.any():
        points = gpd.GeoDataFrame(
            {"_row": out.index[valid]},
            geometry=gpd.points_from_xy(lon[valid], lat[valid]),
            crs="EPSG:4326",
        )
        # A few polygons may share boundaries; the more specific/smaller
        # polygon wins and never duplicates a listing row.
        polys = neighborhoods[["name", "geometry"]].copy()
        polys["_area"] = polys.to_crs("EPSG:32618").geometry.area
        hits = gpd.sjoin(points, polys, how="inner", predicate="intersects")
        hits = hits.sort_values(["_row", "_area", "name"]).drop_duplicates("_row")
        out.loc[hits["_row"].to_numpy(), "neighborhood"] = hits["name"].to_numpy()
    print(
        f"🏘️ Neighborhoods: {out['neighborhood'].notna().sum()}/{len(out)} "
        "listing/property rows assigned using 2010 source polygons"
    )
    return out
