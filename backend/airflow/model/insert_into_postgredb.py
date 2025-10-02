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

    for col in ["walk_routes", "bike_routes", "drive_routes"]:
        df[col] = df[col].apply(
            lambda x: x.wkt if isinstance(x, LineString) else x
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
                    if x.startswith('[') and x.endswith(']'):
                        try:
                            import ast
                            parsed = ast.literal_eval(x)
                            return json.dumps(parsed)
                        except (ValueError, SyntaxError):
                            return json.dumps([x])
                    else:
                        return json.dumps([x])
            else:
                return json.dumps([str(x)])
        except (ValueError, TypeError):
                pass
    
    for col in ["Amenities", "ListingPhotos"]:
        if col in df.columns:
            df[col] = df[col].apply(clean_json_field)

    for col in ["HasValidCertificateOfOccupancy","MeetsMinimumRequirements","ExceedsRequirements","HasFireResistantConstructionType","SatisfiesApplicableCode"]:
        df[col] = df[col].astype(bool)

    df["nearest_neighbor_listingIds"] = df["nearest_neighbor_listingIds"].apply(
        lambda x: json.dumps(x) if isinstance(x, (list, dict)) else x
    )

    df = df[["ListingId", "ListingAddress", "ListingCity", "ListingZip", "CreateDate", "ShortDescription", "RentAmount", "RentType", "Pets", "Amenities", "Bedrooms", "Bathrooms", "HousingType", "latitude", "longitude", "ListingPhotos",  "walk_time", "walk_routes", "bike_time", "bike_routes", "drive_time", "drive_routes", "transit_score", "amenities_score", "OverallSafetyRatingPct", "RentAmountAdjusted", "PredictedRent", "DifferenceinFairValue", "predicted_rent_cma", "nearest_neighbor_listingIds", "rent_per_person", "num_people"]]

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r"[^\w]", "", regex=True)  
        .str.replace("_pct", "pct")
    )

    with engine.begin() as conn: 
        conn.execute(text("TRUNCATE TABLE housing_listings RESTART IDENTITY CASCADE;"))
        
        try:
            df.to_sql("housing_listings", con=conn, if_exists="append", index=False)
            print("✅ Data inserted successfully using to_sql")
        except Exception as e:
            print(f"❌ Error during data insertion: {e}")
            print("Attempting to fix data issues...")
            
            df_clean = df.copy()
            
            for col in ["amenities", "listingphotos", "nearest_neighbor_listingids"]:
                if col in df_clean.columns:
                    df_clean[col] = df_clean[col].astype(str).str.replace("'", '"').replace('""', '"')
            
            df_clean.to_sql("housing_listings", con=conn, if_exists="append", index=False)
            print("✅ Data inserted successfully after cleanup")

def confirmation():
    print("Confirmed Pipeline Complete!")