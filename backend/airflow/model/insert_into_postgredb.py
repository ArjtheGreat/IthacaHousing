import os
import pandas as pd
from sqlalchemy import create_engine, text
from shapely import LineString

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

    for col in ["HasValidCertificateOfOccupancy","MeetsMinimumRequirements","ExceedsRequirements","HasFireResistantConstructionType","SatisfiesApplicableCode"]:
        df[col] = df[col].astype(bool)

    df = df[["ListingId", "ListingAddress", "ListingCity", "ListingZip", "CreateDate", "ShortDescription", "RentAmount", "RentType", "Pets", "Amenities", "Bedrooms", "Bathrooms", "HousingType", "latitude", "longitude", "ListingPhotos",  "walk_time", "walk_routes", "bike_time", "bike_routes", "drive_time", "drive_routes", "transit_score", "amenities_score", "OverallSafetyRatingPct", "RentAmountAdjusted", "PredictedRent", "DifferenceinFairValue", "predicted_rent_cma", "nearest_neighbor_listingIds"]]

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r"[^\w]", "", regex=True)  
        .str.replace("_pct", "pct")
    )



    with engine.begin() as conn: 
        df.head(0).to_sql("housing_listings", con=conn, if_exists="append", index=False)
        conn.execute(text("TRUNCATE TABLE housing_listings RESTART IDENTITY CASCADE;"))
        df.to_sql("housing_listings", con=conn, if_exists="append", index=False)  

    print("✅ Data inserted successfully using to_sql")

def confirmation():
    print("Confirmed Pipeline Complete!")