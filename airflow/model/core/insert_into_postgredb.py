import os
import json
import re
import ast
import pandas as pd
from sqlalchemy import create_engine, text

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


def psql_insert_copy(df):
    """
    Insert cleaned housing listing data into Supabase (PostgreSQL).
    """
    engine = create_engine(
        os.getenv("DB_URI"),
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_size=1,
        max_overflow=0,
        connect_args={
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        },
    )

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
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(r"[^\w]", "", regex=True)
        .str.replace("_pct", "pct")
    )
    
    df = df.loc[:, ~df.columns.duplicated(keep='first')]

    df = normalize_safety_for_db(df)

    base_columns = [
        "listingid", "listingaddress", "listingcity", "listingzip", "createdate",
        "shortdescription", "rentamount", "renttype", "dateavailable", "unitnumber",
        "listingtypes", "listingexpirationdate", "lengthavailable", "pets", "amenities",
        "bedrooms", "bathrooms", "available_bedrooms", "available_bathrooms",
        "housingtype", "latitude", "longitude", "listingphotos", "transit_score",
        "amenities_score", "predictedrent", "differenceinfairvalue",
        "predicted_rent_cma", "nearest_neighbor_listingids", "rent_per_person",
        "num_people", "total_rent_amount", "owner_name", "nearest_stop_name",
        "walk_time_to_nearest_stop", "transit_time_to_ag_quad",
        "transit_time_to_arts_quad", "transit_time_to_eng_quad",
        "iso15", "neighborhood", "neighborhood_assessment", "property_depth",
        "property_frontage", "property_acres", "property_pc", "water_access",
        "sewer_access", "sewer_name", "year_built", "assessment_sqft", "sale_price",
        "valid_certificate_of_compliance",
    ]

    travel_time_cols = [
        "walk_time_urishall", "walk_time_agriculturequad", "walk_time_artsquad", "walk_time_engineeringquad",
        "bike_time_urishall", "bike_time_agriculturequad", "bike_time_artsquad", "bike_time_engineeringquad",
        "drive_time_urishall", "drive_time_agriculturequad", "drive_time_artsquad", "drive_time_engineeringquad",
    ]

    available_columns = [c for c in base_columns + travel_time_cols if c in df.columns]

    df = df[available_columns].copy() if available_columns else df.copy()

    # createdate is NOT NULL; scrape has no CreateDate — stamp insert time.
    from datetime import datetime, timezone
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

    with engine.begin() as conn:
        # Migrate legacy integer PK → text for composite unit IDs (idempotent).
        conn.execute(text("""
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
        """))
        conn.execute(text("TRUNCATE TABLE housing_listings RESTART IDENTITY CASCADE;"))
        print("🧹 Table truncated successfully")

    print(f"📋 Columns being inserted: {list(df.columns)}")

    placeholders = [f":{col}" for col in df.columns]
    insert_query = text(f"""
        INSERT INTO housing_listings ({", ".join(df.columns)})
        VALUES ({", ".join(placeholders)})
    """)

    records = df.where(pd.notnull(df), None).to_dict(orient="records")

    for record in records:
        for col in ["amenities", "listingphotos", "nearest_neighbor_listingids"]:
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
            if isinstance(v, float) and pd.isna(v):
                record[k] = None
        record = convert_property_fields(record)
        record = convert_date_fields(record)

    with engine.begin() as conn:
        conn.execute(insert_query, records)
        print(f"✅ Inserted {len(records)} rows into housing_listings")

def confirmation(): 
    print("Confirmed Pipeline Complete!")

