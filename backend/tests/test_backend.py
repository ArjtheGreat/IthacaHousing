import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
import numpy as np
import os
from pathlib import Path
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import random
from typing import List


BASE_DIR = Path(__file__).resolve().parent.parent  
sys.path.append(str(BASE_DIR))

from main import app
from db import get_db, HousingListing, Base

DB_URI = os.getenv("DB_URI")
TEST_DATABASE_URL = (
    {DB_URI}
)

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Create tables once for all tests"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def override_get_db():
    """
    Provides a clean database session per test function.
    Rolls back any changes after each test.
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

@pytest.fixture(scope="session", autouse=True)
def seed_test_data(setup_db):  
    db = TestingSessionLocal()
    db.query(HousingListing).delete()
    db.add_all(mock_listings(20))
    db.commit()
    db.close()

@pytest.fixture(scope="function")
def client(override_get_db):
    """
    Provides a test client with DB override.
    """
    app.dependency_overrides[get_db] = lambda: override_get_db
    return TestClient(app)

def mock_listing(**kwargs):
    """
    Mock test setup
    """
    return HousingListing(
        **kwargs
    )

def mock_listings(n: int = 10) -> List[HousingListing]:
    """
    Returns a list of n mock HousingListing objects for test cases,
    with randomized but reasonable values.
    """
    housing_types = ["Rent", "Room to Rent", "Shared"]
    pets_options = ["Yes", "No"]

    listings = []

    for i in range(n):
        listings.append(mock_listing(
            listingid=i + 1,
            bedrooms=random.randint(1, 5),
            bathrooms=round(random.choice([1.0, 1.5, 2.0, 2.5, 3.0, 3.5]), 1),
            pets=random.choice(pets_options),
            avg_walking_time=random.randint(5, 20),
            transit_score=random.randint(40, 100),
            housingtype=random.choice(housing_types),
            rentamount=round(random.uniform(800, 3000), 2),
            predictedrent=round(random.uniform(800, 3000), 2),
            rentamountadjusted=round(random.uniform(800, 3000), 2),
            latitude=42.44 + random.uniform(-0.01, 0.01),
            longitude=-76.5 + random.uniform(-0.01, 0.01)
        ))

    return listings

def test_get_listings(client):
    """
    Test case for getting all listings
    """
    res = client.get("/listings/")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_get_top_ten_listings(client):
    """
    Test case for getting top 10 listings
    """ 
    res = client.get("/top-ten-listings/")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 10

def test_get_listing_beds(client):
    """
    Test case for getting all listing with n number of beds
    """ 
    res = client.get("/listing/beds/2")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert all(listing["bedrooms"] == 2 for listing in data)
    

def test_get_listing_baths(client):
    """
    Test case for getting all listing with n number of baths
    """ 
    res = client.get("/listing/baths/3")  # 3/2 = 1.5
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert data[0]["bathrooms"] == 1.5

def test_get_listing_walk(client):
    """
    Test case for getting all listing with walkability score
    """ 
    res = client.get("/listing/walks")
    assert res.status_code == 200
    data = res.json()
    assert all(listing["avg_walking_time"] < 15 for listing in data)


def test_get_listing_transit(client):
    """
    Test case for getting all listing with transit score
    """ 
    res = client.get("/listing/transit")
    assert res.status_code == 200
    data = res.json()
    assert all(listing["transit_score"] > 60 for listing in data)

def test_get_listing_pet(client):
    """
    Test case for getting all listing with pet score
    """ 
    res = client.get("/listing/pets")
    assert res.status_code == 200
    data = res.json()
    assert all(listing["pets"] == "Yes" for listing in data)


def test_get_listing_by_id(client):
    """
    Test case for getting a listing by its id
    """ 
    res = client.get("/listing/1")
    assert res.status_code == 200
    data = res.json()
    assert data["listingid"] == 1

def test_get_cluster_neighborhoods(client):
    """
    Test case for clustering neighborhoods
    """ 
    res = client.get("/clusters/")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_get_heatmap_neighborhoods(client):
    """
    Test case for heatmap of neighborhoods
    """ 
    res = client.get("/heatmap/")
    assert res.status_code == 200
    assert "heat_data" in res.json()

def test_metrics_endpoint(client):
    """
    Test case for metrics for Prometheus/Grafana
    """ 
    res = client.get("/metrics")
    assert res.status_code == 200
    assert b"prediction_error" in res.content
