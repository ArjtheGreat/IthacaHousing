import requests
import pandas as pd
import numpy as np
import time
from airflow.models import Variable
from airflow.utils.dates import days_ago
import geocoder
import ast
import json
import os

if os.path.exists("/opt/airflow/model"):
    BASE_DIR = "/opt/airflow/model"  
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_PATH = os.path.join(BASE_DIR, "latest_listings.csv")

def fetch_active_listings():
    """Fetches Active Listings from Cornell Off-Campus Housing API"""
    url = "https://listings.offcampusliving.cornell.edu/api/activeListings"
    response = requests.get(url)
    data = response.json()
    
    housing_data_df = pd.DataFrame(data)
    housing_data_df["SafetyRatings"] = housing_data_df["SafetyRatings"].apply(
        lambda x: json.dumps(x) if isinstance(x, dict) else x
    )

    housing_data_df.to_csv(DATA_PATH, index=False)
    return housing_data_df

def housing_data_preprocessing():
    """Preprocesses House Data (extracts Lat, Lng)"""
    housing_data_df = pd.read_csv(DATA_PATH)
    housing_data_df[['latitude', 'longitude']] = housing_data_df.apply(lambda row: pd.Series(geocoder.get_coordinates(row)), axis=1)
    housing_data_df.replace({"latitude": "", "longitude": "", "None": np.nan}, inplace=True)
    apartments_for_rent = housing_data_df.dropna(subset=["latitude", "longitude"])

    apartments_for_rent["Bedrooms"] = (
        apartments_for_rent["Bedrooms"]
        .replace("studio", 1)
        .apply(pd.to_numeric, errors="coerce")
    )
    apartments_for_rent["RentAmount"] = pd.to_numeric(apartments_for_rent["RentAmount"], errors="coerce")
    apartments_for_rent["Bedrooms"] = pd.to_numeric(apartments_for_rent["Bedrooms"], errors="coerce")

    apartments_for_rent.loc[apartments_for_rent["ListingId"] == 4703, "RentType"] = "Price per Person"

    is_per_person = apartments_for_rent["RentType"].str.lower() == "price per person"
    is_room_to_rent = apartments_for_rent["HousingType"].str.lower() == "room to rent"

    apartments_for_rent["RentAmountAdjusted"] = apartments_for_rent["RentAmount"]

    apartments_for_rent.loc[is_per_person & ~is_room_to_rent, "RentAmountAdjusted"] = (
        apartments_for_rent["RentAmount"] * apartments_for_rent["Bedrooms"]
    )

    apartments_for_rent["Bathrooms"] = pd.to_numeric(apartments_for_rent["Bathrooms"], errors='coerce')
    apartments_for_rent["combined_bedrooms_bathrooms"] = 1.5*apartments_for_rent["Bedrooms"]+apartments_for_rent["Bathrooms"]
    
    print(apartments_for_rent.head())
    return apartments_for_rent