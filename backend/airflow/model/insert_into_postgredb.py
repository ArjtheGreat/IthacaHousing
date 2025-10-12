import os
import pandas as pd
from sqlalchemy import create_engine, text
from shapely import LineString
import json

def psql_insert_copy(df):
    """
    Insert into Supabase
    """
    # DB_USER=os.getenv("DB_USER")
    # DB_PWD=os.getenv("DB_PWD", "3789mwPK")
    # DB_HOST=os.getenv("DB_HOST")
    # DB_PORT=os.getenv("DB_PORT")
    # DB_NAME=os.getenv("DB_NAME")

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


    def clean_json_field(x):
        """Clean and format JSON fields properly"""
        if x is None:
            return None

        try:
            if pd.isna(x):
                return None
            elif isinstance(x, (list, dict)):
                return json.dumps(x)
            elif isinstance(x, str):
                try:
                    parsed = json.loads(x)
                    return json.dumps(parsed)
                except (json.JSONDecodeError, ValueError):
                    cleaned = x
                    import re
                    cleaned = re.sub(r'([^\\])"([^":,}\]]*)"([^":,}\]]*)', r'\1\\"\2\\"\3', cleaned)
                    cleaned = re.sub(r'"([^":,}\]]*)"([^":,}\]]*)', r'\\"\1\\"\2', cleaned)
                    
                    try:
                        parsed = json.loads(cleaned)
                        return json.dumps(parsed)
                    except (json.JSONDecodeError, ValueError):
                        if cleaned.startswith('[') and cleaned.endswith(']'):
                            try:
                                import ast
                                parsed = ast.literal_eval(cleaned)
                                return json.dumps(parsed)
                            except (ValueError, SyntaxError):
                                pass
                        escaped_str = str(x).replace('\\', '\\\\').replace('"', '\\"')
                        return json.dumps([escaped_str])
            else:
                return json.dumps([str(x)])
        except (ValueError, TypeError):
            return None
    
    for col in ["Amenities", "ListingPhotos"]:
        if col in df.columns:
            df[col] = df[col].apply(clean_json_field)

    for col in ["HasValidCertificateOfOccupancy","MeetsMinimumRequirements","ExceedsRequirements","HasFireResistantConstructionType","SatisfiesApplicableCode"]:
        if col in df.columns:
            df[col] = df[col].astype(bool)

    df["nearest_neighbor_listingIds"] = df["nearest_neighbor_listingIds"].apply(
        lambda x: json.dumps(x) if isinstance(x, (list, dict)) else x
    )

    safety_col = None
    if "valid_certificate_of_compliance" in df.columns:
        safety_col = "valid_certificate_of_compliance"
    elif "OverallSafetyRatingPct" in df.columns:
        safety_col = "OverallSafetyRatingPct"
    elif "overallsafetyratingpct" in df.columns:
        safety_col = "overallsafetyratingpct"

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r"[^\w]", "", regex=True)  
        .str.replace("_pct", "pct")
    )
    
    base_columns = ["listingid", "listingaddress", "listingcity", "listingzip", "createdate", "shortdescription", "rentamount", "renttype", "pets", "amenities", "bedrooms", "bathrooms", "available_bedrooms", "available_bathrooms", "housingtype", "latitude", "longitude", "listingphotos", "transit_score", "amenities_score", "predictedrent", "differenceinfairvalue", "predicted_rent_cma", "nearest_neighbor_listingids", "rent_per_person", "num_people", "total_rent_amount", "owner_name", "nearest_stop_name", "walk_time_to_nearest_stop", "transit_time_to_ag_quad", "transit_time_to_arts_quad", "transit_time_to_eng_quad", "iso15", "neighborhood"]
    
    if safety_col:
        base_columns.append(safety_col)
    
    new_travel_columns = [
        "walk_time_urishall", "walk_time_agriculturequad", "walk_time_artsquad", "walk_time_engineeringquad",
        "bike_time_urishall", "bike_time_agriculturequad", "bike_time_artsquad", "bike_time_engineeringquad",
        "drive_time_urishall", "drive_time_agriculturequad", "drive_time_artsquad", "drive_time_engineeringquad"
    ]
    
    available_columns = [col for col in base_columns + new_travel_columns if col in df.columns]
    df = df[available_columns]

    
    def refresh_housing_listings(df, engine):
        """
        Refresh the housing_listings table with new data using parameterized SQL inserts.
        Compatible with pandas 2.x + SQLAlchemy 2.x + PostgreSQL.
        """

        # 1️⃣ Truncate table
        with engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE housing_listings RESTART IDENTITY CASCADE;"))
            print("🧹 Table truncated successfully")

        # Debug: Print actual columns in the DataFrame
        print(f"📋 Columns in DataFrame at INSERT time: {list(df.columns)}")
        
        safety_col_in_sql = None
        if "valid_certificate_of_compliance" in df.columns:
            safety_col_in_sql = "valid_certificate_of_compliance"
        elif "overallsafetyratingpct" in df.columns:
            safety_col_in_sql = "overallsafetyratingpct"
        
        base_cols = [
            "listingid", "listingaddress", "listingcity", "listingzip", "createdate", "shortdescription",
            "rentamount", "renttype", "pets", "amenities", "bedrooms", "bathrooms", "available_bedrooms",
            "available_bathrooms", "housingtype", "latitude", "longitude", "listingphotos", "transit_score", 
            "amenities_score", "predictedrent", "differenceinfairvalue", 
            "predicted_rent_cma", "nearest_neighbor_listingids", "rent_per_person", "num_people", 
            "total_rent_amount", "owner_name", "nearest_stop_name", "walk_time_to_nearest_stop", 
            "transit_time_to_ag_quad", "transit_time_to_arts_quad", "transit_time_to_eng_quad",
        ]
        
        if safety_col_in_sql:
            base_cols.insert(20, safety_col_in_sql)
        
        # Add neighborhood if it exists in the dataframe
        if "neighborhood" in df.columns:
            base_cols.insert(base_cols.index("nearest_stop_name"), "neighborhood")
        
        travel_time_cols = [
            "walk_time_urishall", "walk_time_agriculturequad", "walk_time_artsquad", "walk_time_engineeringquad",
            "bike_time_urishall", "bike_time_agriculturequad", "bike_time_artsquad", "bike_time_engineeringquad",
            "drive_time_urishall", "drive_time_agriculturequad", "drive_time_artsquad", "drive_time_engineeringquad"
        ]
        
        for col in travel_time_cols:
            if col in df.columns:
                base_cols.append(col)
        
        isochronic_cols = ["iso15"]
        for col in isochronic_cols:
            if col in df.columns:
                base_cols.append(col)
        
        values_placeholders = [f":{col}" for col in base_cols]
        
        insert_query = text(f"""
             INSERT INTO housing_listings ({", ".join(base_cols)}) 
             VALUES ({", ".join(values_placeholders)})
         """)

        records = df.to_dict(orient="records")

        for record in records:
            for col in ["amenities", "listingphotos", "nearest_neighbor_listingids"]:
                if col in record and pd.notna(record[col]):
                    record[col] = clean_json_field(record[col])
                else:
                    record[col] = None

        with engine.begin() as conn:
            conn.execute(insert_query, records)
            print(f"✅ Inserted {len(records)} rows into housing_listings")
    
    refresh_housing_listings(df, engine)

def confirmation():
    print("Confirmed Pipeline Complete!")