import os
import json
import re
import ast
import time
from datetime import datetime, timezone
from decimal import Decimal

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, DBAPIError

from calculators.calculate_amenity_score import CANONICAL_AMENITY_COLUMNS
from core.excluded_listing_unit_ids import exclude_listing_units

# Predictors that are built in memory for the rent model. Spaced amenity
# names are renamed here so the insert sanitizer does not collapse them
# into names like "electricityincluded".
MODEL_FEATURE_COLUMN_MAP = {
    "combined_bedrooms_bathrooms": "combined_bedrooms_bathrooms",
    "YR_BUILT_ENCODED": "yr_built_encoded",
    "Electricity Included": "electricity_included",
    "Heat Included": "heat_included",
    "Water Included": "water_included",
    "Internet Included": "internet_included",
    "Laundry Facilities": "laundry_facilities",
    "Air Conditioning": "air_conditioning",
    "Furnished": "furnished",
}


def ensure_model_feature_columns(engine):
    """Add rent-model predictor columns to an existing housing_listings table."""
    _execute_with_retry(
        engine,
        text("""
            ALTER TABLE housing_listings
                ADD COLUMN IF NOT EXISTS combined_bedrooms_bathrooms numeric,
                ADD COLUMN IF NOT EXISTS yr_built_encoded integer,
                ADD COLUMN IF NOT EXISTS electricity_included integer,
                ADD COLUMN IF NOT EXISTS heat_included integer,
                ADD COLUMN IF NOT EXISTS water_included integer,
                ADD COLUMN IF NOT EXISTS internet_included integer,
                ADD COLUMN IF NOT EXISTS laundry_facilities integer,
                ADD COLUMN IF NOT EXISTS air_conditioning integer,
                ADD COLUMN IF NOT EXISTS furnished integer;
        """),
        label="model feature columns",
    )
    # Experimental amenity flags are persisted for database-only retraining.
    # Each flag means advertised; missing advertised evidence is encoded as zero.
    additions = ", ".join(f"ADD COLUMN IF NOT EXISTS {c} integer" for c in CANONICAL_AMENITY_COLUMNS)
    _execute_with_retry(engine, text(f"ALTER TABLE housing_listings {additions}"), label="canonical amenity columns")




# These legacy fields are deliberately hidden from the curated browsing view,
# not dropped: other services still read them or rely on the baseline model.
# The underlying housing_listings table remains the stable API contract.
CLEAN_VIEW_NAME = "housing_listings_clean"
CLEAN_VIEW_EXCLUDE = {"amenities_score"}


def create_clean_listing_view(engine, preferred_order):
    """Expose cleaned, logically ordered listing columns in Supabase's table UI.

    No destructive table rebuild or DROP COLUMN. On each full ingest the view is
    recreated from the columns that actually exist. Query the underlying table
    for legacy consumers.
    """
    with engine.connect() as conn:
        available = {
            row[0] for row in conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = 'housing_listings'"
            ))
        }
    columns = [name for name in preferred_order
               if name in available and name not in CLEAN_VIEW_EXCLUDE]
    if not columns:
        raise ValueError("Cannot build housing_listings_clean: no recognized columns")
    # Every identifier comes from a static trusted whitelist, not user input.
    projection = ", ".join(f'"{name}"' for name in columns)
    # CREATE OR REPLACE can fail when existing view order changes, so DROP
    # without CASCADE. If dependent objects exist, fail explicitly rather
    # than destroying them.
    _execute_with_retry(
        engine,
        text(f'DROP VIEW IF EXISTS public."{CLEAN_VIEW_NAME}"; '
             f'CREATE VIEW public."{CLEAN_VIEW_NAME}" WITH (security_invoker = true) AS '
             f'SELECT {projection} FROM public.housing_listings'),
        label="refresh organized housing listings view",
    )
    print(f"🧾 Refreshed {CLEAN_VIEW_NAME}: {len(columns)} ordered columns")

def clean_json_field(x):
    """
    Clean and standardize JSON-like values for SQL insertion.
    """
    if x is None or pd.isna(x):
        return None

    try:
        if isinstance(x, (list, dict)):
            return json.dumps(x)

        if isinstance(x, str):
            try:
                parsed = json.loads(x)
                return json.dumps(parsed)
            except (json.JSONDecodeError, ValueError):
                cleaned = re.sub(r'([^\\])"([^":,}\]]*)"([^":,}\]]*)', r'\1\\"\2\\"\3', x)
                cleaned = re.sub(r'"([^":,}\]]*)"([^":,}\]]*)', r'\\"\1\\"\2', cleaned)

                try:
                    parsed = json.loads(cleaned)
                    return json.dumps(parsed)
                except (json.JSONDecodeError, ValueError):
                    if cleaned.startswith("[") and cleaned.endswith("]"):
                        try:
                            parsed = ast.literal_eval(cleaned)
                            return json.dumps(parsed)
                        except (ValueError, SyntaxError):
                            pass
                    escaped_str = x.replace("\\", "\\\\").replace('"', '\\"')
                    return json.dumps([escaped_str])
        return json.dumps([str(x)])
    except (ValueError, TypeError):
        return None


def convert_property_fields(record):
    """
    Convert numeric, string, and date property detail fields safely.
    """
    converters = {
        'neighborhood_assessment': lambda x: int(x) if pd.notna(x) and x > 0 else None,
        'property_depth': lambda x: float(x) if pd.notna(x) and x > 0 else None,
        'property_frontage': lambda x: float(x) if pd.notna(x) and x > 0 else None,
        'property_acres': lambda x: float(x) if pd.notna(x) and x > 0 else None,
        'property_pc': lambda x: str(x) if pd.notna(x) else None,
        'water_access': lambda x: str(x) if pd.notna(x) else None,
        'sewer_access': lambda x: str(x) if pd.notna(x) else None,
        'sewer_name': lambda x: str(x) if pd.notna(x) else None,
        'year_built': lambda x: int(x) if pd.notna(x) and x > 0 else None,
        'assessment_sqft': lambda x: float(x) if pd.notna(x) and x > 0 else None,
        'sale_price': lambda x: float(x) if pd.notna(x) and x > 0 else None
    }

    for col, func in converters.items():
        if col in record:
            try:
                record[col] = func(record[col])
            except (ValueError, TypeError):
                record[col] = None
    return record


def convert_date_fields(record):
    """
    Convert date fields to proper datetime format for database insertion.
    """
    from datetime import datetime
    
    date_fields = ['createdate', 'dateavailable', 'listingexpirationdate']
    
    for field in date_fields:
        if field in record and pd.notna(record[field]) and record[field] is not None:
            try:
                # Try to parse the date string
                if isinstance(record[field], str):
                    record[field] = pd.to_datetime(record[field])
                elif isinstance(record[field], (pd.Timestamp, datetime)):
                    record[field] = pd.to_datetime(record[field])
            except (ValueError, TypeError):
                record[field] = None
        else:
            record[field] = None
    
    return record


def get_safety_col(df):
    """
    Return the name of whichever safety column exists.
    """
    for c in ["valid_certificate_of_compliance", "OverallSafetyRatingPct", "overallsafetyratingpct"]:
        if c in df.columns:
            return c
    return None


def normalize_safety_for_db(df):
    """
    housing_listings only has valid_certificate_of_compliance (int 0/1).
    Map scraped OverallSafetyRatingPct / certificate flags onto that column.
    """
    if "valid_certificate_of_compliance" in df.columns:
        df["valid_certificate_of_compliance"] = (
            pd.to_numeric(df["valid_certificate_of_compliance"], errors="coerce")
            .fillna(0)
            .astype(int)
        )
        return df

    if "hasvalidcertificateofoccupancy" in df.columns:
        df["valid_certificate_of_compliance"] = (
            pd.to_numeric(df["hasvalidcertificateofoccupancy"], errors="coerce")
            .fillna(0)
            .astype(int)
        )
    elif "overallsafetyratingpct" in df.columns:
        pct = pd.to_numeric(df["overallsafetyratingpct"], errors="coerce").fillna(0)
        df["valid_certificate_of_compliance"] = (pct > 0).astype(int)
    else:
        df["valid_certificate_of_compliance"] = 0

    return df


def _sanitize_record_value(v):
    if v is None:
        return None
    if isinstance(v, float) and pd.isna(v):
        return None
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, pd.Timestamp):
        return v.to_pydatetime()
    if isinstance(v, datetime):
        return v
    return v


def _chunked(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def _execute_with_retry(engine, statement, params=None, attempts=4, label="query"):
    """Retry on transient SSL / connection drops (common with Supabase pooler)."""
    last_err = None
    for attempt in range(1, attempts + 1):
        try:
            with engine.begin() as conn:
                if params is None:
                    conn.execute(statement)
                else:
                    conn.execute(statement, params)
            return
        except (OperationalError, DBAPIError) as e:
            last_err = e
            msg = str(e).lower()
            transient = any(
                s in msg
                for s in (
                    "ssl syscall",
                    "eof detected",
                    "connection reset",
                    "server closed the connection",
                    "connection timed out",
                    "could not receive data",
                    "ssl connection has been closed",
                )
            )
            if not transient or attempt == attempts:
                raise
            wait = min(2 ** attempt, 20)
            print(
                f"⚠️ {label} failed (attempt {attempt}/{attempts}): {e}. "
                f"Retrying in {wait}s..."
            )
            try:
                engine.dispose()
            except Exception:
                pass
            time.sleep(wait)
    raise last_err


def psql_insert_copy(df):
    """
    Insert cleaned housing listing data into Supabase (PostgreSQL).
    Batches rows to avoid SSL EOF on large single executemany payloads.
    """
    df = exclude_listing_units(df)
    engine = create_engine(
        os.getenv("DB_URI"),
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=1,
        max_overflow=0,
        connect_args={
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
            "connect_timeout": 30,
        },
    )
    ensure_model_feature_columns(engine)

    for col in ["Amenities", "ListingPhotos"]:
        if col in df.columns:
            df[col] = df[col].apply(clean_json_field)

    bool_cols = [
        "HasValidCertificateOfOccupancy", "MeetsMinimumRequirements",
        "ExceedsRequirements", "HasFireResistantConstructionType",
        "SatisfiesApplicableCode"
    ]
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].astype(bool)

    if "nearest_neighbor_listingIds" in df.columns:
        df["nearest_neighbor_listingIds"] = df["nearest_neighbor_listingIds"].apply(
            lambda x: json.dumps(x) if isinstance(x, (list, dict)) else x
        )
    for src, dest in MODEL_FEATURE_COLUMN_MAP.items():
        if src in df.columns and src != dest:
            if dest in df.columns:
                df = df.drop(columns=[src])
            else:
                df = df.rename(columns={src: dest})
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(r"[^\w]", "", regex=True)
        .str.replace("_pct", "pct")
    )
    
    df = df.loc[:, ~df.columns.duplicated(keep='first')]

    df = normalize_safety_for_db(df)

    # Keep source floor-plan area separate from parcel assessment_sqft.
    # Older CSV exports used "SqFt" (normalized to "sqft").
    if "unit_sqft" not in df.columns and "sqft" in df.columns:
        df["unit_sqft"] = df["sqft"]
    if "unit_sqft" in df.columns:
        area = pd.to_numeric(df["unit_sqft"], errors="coerce")
        df["unit_sqft"] = area.where(area > 0)

    # One explicit insertion contract. Groups also define the friendly column
    # order in housing_listings_clean; don't rely on physical ALTER TABLE order.
    # Keep legacy fields consumed by the API/frontend until those clients migrate.
    listing_groups = {
        "identity": [
            "listingid", "listingaddress", "listingcity", "listingzip",
            "housingtype", "unitnumber", "listingtypes", "shortdescription",
            "listingphotos", "createdate", "dateavailable",
            "listingexpirationdate", "lengthavailable",
        ],
        "pricing": [
            "rentamount", "renttype", "rent_per_person",
            "rent_per_person_original", "num_people", "total_rent_amount",
            "predictedrent", "differenceinfairvalue", "predicted_rent_cma",
            "nearest_neighbor_listingids", "ithaca_insights_adjustment",
            "suspected_landlord_pricing_error", "pricing_adjustment_reason",
        ],
        "floorplan": [
            "bedrooms", "bathrooms", "available_bedrooms",
            "available_bathrooms", "combined_bedrooms_bathrooms",
            "unit_sqft",
        ],
        "location": [
            "latitude", "longitude", "neighborhood", "iso15",
            "walk_time_urishall", "walk_time_agriculturequad",
            "walk_time_artsquad", "walk_time_engineeringquad",
            "bike_time_urishall", "bike_time_agriculturequad",
            "bike_time_artsquad", "bike_time_engineeringquad",
            "drive_time_urishall", "drive_time_agriculturequad",
            "drive_time_artsquad", "drive_time_engineeringquad",
            "nearest_stop_name", "walk_time_to_nearest_stop",
            "transit_time_to_ag_quad", "transit_time_to_arts_quad",
            "transit_time_to_eng_quad", "transit_score",
            "food_count_200m", "food_nearest_dist",
            "attractions_count_200m", "attractions_nearest_dist",
            "shopping_count_200m", "shopping_nearest_dist",
            "grocery_count_200m", "grocery_nearest_dist",
        ],
        "property": [
            "year_built", "yr_built_encoded",
            "valid_certificate_of_compliance", "owner_name",
            "landlord_email", "landlord_name", "landlord_full_name",
            "landlord_username", "contact_number",
            "neighborhood_assessment", "assessment_sqft", "sale_price",
            "property_depth", "property_frontage", "property_acres",
            "property_pc", "water_access", "sewer_access", "sewer_name",
        ],
        "amenities": [
            "amenities", "pets",
            # Legacy exact-match values retained while frontend and baseline
            # still consume them; the normalized flags are independent.
            "amenities_score", "electricity_included", "heat_included",
            "water_included", "internet_included", "laundry_facilities",
            "air_conditioning", "furnished",
            *CANONICAL_AMENITY_COLUMNS,
        ],
    }
    ordered_columns = list(dict.fromkeys(
        col for group in listing_groups.values() for col in group
    ))
    available_columns = [col for col in ordered_columns if col in df.columns]
    ignored_columns = sorted(set(df.columns) - set(ordered_columns))
    if ignored_columns:
        print(f"ℹ️ Skipping {len(ignored_columns)} non-contract columns: {ignored_columns}")

    df = df[available_columns].copy() if available_columns else df.copy()

    # createdate is NOT NULL; scrape has no CreateDate — stamp insert time.
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if "createdate" not in df.columns:
        df["createdate"] = now
        available_columns = ["createdate"] + available_columns
    else:
        df["createdate"] = pd.to_datetime(df["createdate"], errors="coerce")
        df["createdate"] = df["createdate"].fillna(now)

    df = df[available_columns].copy()

    # Unit-level scrape IDs are strings like "7734-17720".
    if "listingid" in df.columns:
        df["listingid"] = df["listingid"].astype(str)

    _execute_with_retry(
        engine,
        text("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'housing_listings'
                      AND column_name = 'listingid'
                      AND data_type IN ('integer', 'bigint', 'smallint')
                ) THEN
                    ALTER TABLE housing_listings
                        ALTER COLUMN listingid TYPE text USING listingid::text;
                END IF;

                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'sold_listings'
                      AND column_name = 'listingid'
                      AND data_type IN ('integer', 'bigint', 'smallint')
                ) THEN
                    ALTER TABLE sold_listings
                        ALTER COLUMN listingid TYPE text USING listingid::text;
                END IF;
            END $$;
        """),
        label="schema migrate",
    )

    # Add adjustment audit fields to existing databases before inserting rows.
    # These flags indicate a heuristic correction, not a proven landlord error.
    _execute_with_retry(
        engine,
        text("""
            ALTER TABLE housing_listings
                ADD COLUMN IF NOT EXISTS rent_per_person_original numeric,
                ADD COLUMN IF NOT EXISTS ithaca_insights_adjustment boolean NOT NULL DEFAULT false,
                ADD COLUMN IF NOT EXISTS suspected_landlord_pricing_error boolean NOT NULL DEFAULT false,
                ADD COLUMN IF NOT EXISTS pricing_adjustment_reason text,
                ADD COLUMN IF NOT EXISTS landlord_email text,
                ADD COLUMN IF NOT EXISTS landlord_name text,
                ADD COLUMN IF NOT EXISTS landlord_full_name text,
                ADD COLUMN IF NOT EXISTS landlord_username text,
                ADD COLUMN IF NOT EXISTS contact_number text,
                ADD COLUMN IF NOT EXISTS food_count_200m numeric,
                ADD COLUMN IF NOT EXISTS food_nearest_dist numeric,
                ADD COLUMN IF NOT EXISTS attractions_count_200m numeric,
                ADD COLUMN IF NOT EXISTS attractions_nearest_dist numeric,
                ADD COLUMN IF NOT EXISTS shopping_count_200m numeric,
                ADD COLUMN IF NOT EXISTS shopping_nearest_dist numeric,
                ADD COLUMN IF NOT EXISTS grocery_count_200m numeric,
                ADD COLUMN IF NOT EXISTS grocery_nearest_dist numeric,
                ADD COLUMN IF NOT EXISTS unit_sqft numeric;
        """),
        label="rent adjustment schema migrate",
    )

    print(f"📋 Columns being inserted: {list(df.columns)}")
    missing_optional = [c for c in ("iso15", "neighborhood") if c not in df.columns]
    if missing_optional:
        print(f"⚠️ Optional columns missing from frame (not inserted): {missing_optional}")

    placeholders = [f":{col}" for col in df.columns]
    insert_query = text(f"""
        INSERT INTO housing_listings ({", ".join(df.columns)})
        VALUES ({", ".join(placeholders)})
    """)

    records = df.where(pd.notnull(df), None).to_dict(orient="records")

    for record in records:
        for col in ["amenities", "listingphotos", "nearest_neighbor_listingids"]:
            if col in record:
                record[col] = clean_json_field(record.get(col))
        if "owner_name" in record:
            owner = record["owner_name"]
            if isinstance(owner, (list, dict)):
                record["owner_name"] = json.dumps(owner) if owner else None
            elif owner is None or (isinstance(owner, float) and pd.isna(owner)):
                record["owner_name"] = None
            else:
                record["owner_name"] = str(owner)
        for k, v in list(record.items()):
            record[k] = _sanitize_record_value(v)
        record = convert_property_fields(record)
        record = convert_date_fields(record)
        for k, v in list(record.items()):
            record[k] = _sanitize_record_value(v)

    # Truncate first (own txn). Then insert in small batches so a pooler
    # SSL drop doesn't wipe a multi-MB single statement.
    _execute_with_retry(
        engine,
        text("TRUNCATE TABLE housing_listings RESTART IDENTITY CASCADE;"),
        label="truncate",
    )
    print("🧹 Table truncated successfully")

    batch_size = 50
    inserted = 0
    for batch_num, batch in enumerate(_chunked(records, batch_size), start=1):
        _execute_with_retry(
            engine,
            insert_query,
            params=batch,
            label=f"insert batch {batch_num}",
        )
        inserted += len(batch)
        if batch_num == 1 or batch_num % 5 == 0 or inserted == len(records):
            print(f"💾 Inserted {inserted}/{len(records)} rows...")

    print(f"✅ Inserted {inserted} rows into housing_listings")
    # A sorted, narrower browsing surface without dropping live API columns.
    # Created after the full ingest so the view always reflects the latest schema.
    # ALTER TABLE ADD COLUMN cannot reorder a PostgreSQL table's existing columns.
    create_clean_listing_view(engine, ordered_columns)


def confirmation(): 
    print("Confirmed Pipeline Complete!")

