import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Numeric, Text, JSON, TypeDecorator, DateTime, func
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.dialects.postgresql import JSONB
import json

load_dotenv()

DB_URI = os.getenv("DB_URI")
if DB_URI is None:
    raise ValueError("DB_URI environment variable is not set. Please check your .env file.")

DATABASE_URL = f"{DB_URI}"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class HousingListing(Base):
    """
    PostgreSQL Database Model for Housing Listings
    """
    __tablename__ = "housing_listings"
    
    listingid = Column(Integer, primary_key=True, index=True)
    listingaddress = Column(String)
    listingcity = Column(String)
    listingzip = Column(String)
    createdate = Column(DateTime, default=func.now(), nullable=False)
    shortdescription = Column(Text)
    rentamount = Column(Numeric)
    renttype = Column(String)
    pets = Column(String)
    amenities = Column(String)
    bedrooms = Column(Numeric)
    bathrooms = Column(Numeric)
    housingtype = Column(String)
    latitude = Column(Numeric)
    longitude = Column(Numeric)
    listingphotos = Column(JSON)
    walk_time = Column(Numeric)
    walk_routes = Column(Text)
    bike_time = Column(Numeric)
    bike_routes = Column(Text)
    drive_time = Column(Numeric)
    drive_routes = Column(Text)
    transit_score = Column(Numeric)
    amenities_score = Column(Numeric)
    overallsafetyratingpct = Column(Numeric)
    predictedrent = Column(Numeric)
    differenceinfairvalue = Column(Numeric)
    predicted_rent_cma = Column(Numeric)
    nearest_neighbor_listingids = Column(Text)
    rent_per_person = Column(Numeric)
    num_people = Column(Numeric)


Base.metadata.create_all(bind=engine)


