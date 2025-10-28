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
    dateavailable = Column(DateTime)
    unitnumber = Column(String)
    listingtypes = Column(String)
    listingexpirationdate = Column(DateTime)
    lengthavailable = Column(Numeric)
    pets = Column(String)
    amenities = Column(String)
    bedrooms = Column(Numeric)
    bathrooms = Column(Numeric)
    available_bedrooms = Column(Numeric)
    available_bathrooms = Column(Numeric)
    housingtype = Column(String)
    latitude = Column(Numeric)
    longitude = Column(Numeric)
    listingphotos = Column(JSON)
    walk_time_urishall = Column(Numeric)
    walk_time_agriculturequad = Column(Numeric)
    walk_time_artsquad = Column(Numeric)
    walk_time_engineeringquad = Column(Numeric)
    bike_time_urishall = Column(Numeric)
    bike_time_agriculturequad = Column(Numeric)
    bike_time_artsquad = Column(Numeric)
    bike_time_engineeringquad = Column(Numeric)
    drive_time_urishall = Column(Numeric)
    drive_time_agriculturequad = Column(Numeric)
    drive_time_artsquad = Column(Numeric)
    drive_time_engineeringquad = Column(Numeric)
    transit_score = Column(Numeric)
    amenities_score = Column(Numeric)
    valid_certificate_of_compliance = Column(Integer)
    predictedrent = Column(Numeric)
    differenceinfairvalue = Column(Numeric)
    predicted_rent_cma = Column(Numeric)
    nearest_neighbor_listingids = Column(Text)
    rent_per_person = Column(Numeric)
    num_people = Column(Numeric)
    total_rent_amount = Column(Numeric)
    owner_name = Column(String)
    neighborhood = Column(String)
    nearest_stop_name = Column(String)
    walk_time_to_nearest_stop = Column(Numeric)
    transit_time_to_ag_quad = Column(Numeric)
    transit_time_to_arts_quad = Column(Numeric)
    transit_time_to_eng_quad = Column(Numeric)
    iso15 = Column(Text)
    
    neighborhood_assessment = Column(Integer)
    property_depth = Column(Numeric)
    property_frontage = Column(Numeric)
    property_acres = Column(Numeric)
    property_pc = Column(String) 
    water_access = Column(String)
    sewer_access = Column(String)
    sewer_name = Column(String)
    year_built = Column(Integer)
    assessment_sqft = Column(Numeric)
    sale_price = Column(Numeric)


Base.metadata.create_all(bind=engine)


