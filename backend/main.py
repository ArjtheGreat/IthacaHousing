from fastapi import FastAPI, Request, Response
import uvicorn
from fastapi import FastAPI, HTTPException, Depends
import traceback
from db import HousingListing, get_db
from sqlalchemy.orm import sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from serializers import serialize_listing, safe_float
import logging
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial import Voronoi
import pandas as pd
from fastapi.responses import JSONResponse
from shapely.geometry import Polygon
import geopandas as gpd
from sqlalchemy import func
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_fastapi_instrumentator.metrics import Info
from prometheus_client import CollectorRegistry, generate_latest, multiprocess, CONTENT_TYPE_LATEST
from prometheus_client import Summary, Gauge
import numpy as np
import os
from pathlib import Path
import sys
from sqlalchemy import text
import math
import json


def safe_float(value):
    """Convert value to float, returning None for NaN, inf, or None values"""
    if value is None:
        return None
    try:
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
)

instrumentator = Instrumentator().instrument(app)
instrumentator.expose(app)

@app.options("/{full_path:path}")
async def preflight_handler():
    return {"message": "Preflight OK"}
 
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logging.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logging.info(f"Response: {response.status_code}")
    return response
 
@app.get("/listings/")
def get_listings(db: Session = Depends(get_db)):
    """
    Gets all listings in Database
    """
    try:
        listings = db.query(HousingListing).all()
        return [serialize_listing(listing) for listing in listings]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e) + "\n" + traceback.format_exc())

@app.get("/listings-minimal/")
def get_listings_minimal(db: Session = Depends(get_db)):
    """
    Get minimal listing data for entire dataset — optimized raw SQL version.
    """
    try:
        query = text("""
            SELECT 
                listingid,
                listingaddress,
                listingcity,
                latitude,
                longitude,
                rent_per_person,
                available_bedrooms,
                rentamount,
                total_rent_amount,
                predictedrent,
                walk_time_urishall,
                walk_time_agriculturequad,
                walk_time_artsquad,
                walk_time_engineeringquad,
                bike_time_urishall,
                bike_time_agriculturequad,
                bike_time_artsquad,
                bike_time_engineeringquad,
                drive_time_urishall,
                drive_time_agriculturequad,
                drive_time_artsquad,
                drive_time_engineeringquad,
                neighborhood
            FROM housing_listings
            WHERE latitude IS NOT NULL 
            AND longitude IS NOT NULL
            AND rent_per_person IS NOT NULL
        """)

        result = db.execute(query)
        rows = result.fetchall()
        
        return [
            {
                "listingid": row[0],
                "listingaddress": row[1],
                "listingcity": row[2],
                "latitude": safe_float(row[3]),
                "longitude": safe_float(row[4]),
                "rent_per_person": safe_float(row[5]),
                "available_bedrooms": safe_float(row[6]),
                "rentamount": safe_float(row[7]),
                "total_rent_amount": safe_float(row[8]),
                "predictedrent": safe_float(row[9]),
                "walk_time_urishall": safe_float(row[10]),
                "walk_time_agriculturequad": safe_float(row[11]),
                "walk_time_artsquad": safe_float(row[12]),
                "walk_time_engineeringquad": safe_float(row[13]),
                "bike_time_urishall": safe_float(row[14]),
                "bike_time_agriculturequad": safe_float(row[15]),
                "bike_time_artsquad": safe_float(row[16]),
                "bike_time_engineeringquad": safe_float(row[17]),
                "drive_time_urishall": safe_float(row[18]),
                "drive_time_agriculturequad": safe_float(row[19]),
                "drive_time_artsquad": safe_float(row[20]),
                "drive_time_engineeringquad": safe_float(row[21]),
                "neighborhood": row[22],
            }
            for row in rows
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/top-ten-listings/")
def get_top_ten_listings(db: Session = Depends(get_db)):
    """
    Gets top ten listings in Database
    """
    top_listings = db.query(HousingListing).order_by(
        ((HousingListing.predictedrent - HousingListing.rent_per_person) / HousingListing.rent_per_person).desc()
    ).limit(10).all()

    return [serialize_listing(listing) for listing in top_listings] 

@app.get("/bottom-ten-listings/")
def get_bottom_ten_listings(db: Session = Depends(get_db)):
    """
    Gets bottom ten listings in Database
    """
    bottom_listings = db.query(HousingListing).order_by(
        ((HousingListing.predictedrent - HousingListing.rent_per_person) / HousingListing.rent_per_person)
    ).limit(10).all()

    return [serialize_listing(listing) for listing in bottom_listings] 

@app.get("/clusters/")
def cluster_neighborhoods(db: Session = Depends(get_db)):
    """
    Clusters Neighborhoods by Price to find "natural pricing neighborhoods"
    """
    listings = db.query(HousingListing.latitude, HousingListing.longitude, HousingListing.rent_per_person).all()

    df = pd.DataFrame(listings, columns=["latitude", "longitude", "rentamount"])

    if df.empty:
        return {"error": "No listings found"}

    Z = linkage(df[["latitude", "longitude"]], method="ward")  
    df["hierarchal_cluster"] = fcluster(Z, t=8, criterion="maxclust")
    df["rentamount_scaled"] = (df["rentamount"] - df["rentamount"].min()) / (df["rentamount"].max() - df["rentamount"].min())

    return df.to_dict(orient="records")

@app.get("/heatmap/")
def heatmap_neighborhoods(db: Session = Depends(get_db)):
    """
    Heatmaps Neighborhoods by Price to find "natural pricing neighborhoods"
    """
    listings = db.query(HousingListing.latitude, HousingListing.longitude, HousingListing.rent_per_person).all()

    df = pd.DataFrame(listings, columns=["latitude", "longitude", "rentamount"])

    if df.empty:
        return {"error": "No listings found"}

    df["rentamount"] = pd.to_numeric(df["rentamount"], errors="coerce")
    df["rentamount_scaled"] = df["rentamount"] / df["rentamount"].max()

    df = df.dropna()  

    heat_data = df[["latitude", "longitude", "rentamount_scaled"]].values.tolist()

    return {"heat_data": heat_data}

@app.get("/voronoi/")
def voronoi_neighborhoods(db: Session = Depends(get_db)):
    """
    Generates Voronoi polygons based on rental pricing data.
    """
    listings = db.query(HousingListing.latitude, HousingListing.longitude, HousingListing.rent_per_person).all()

    df = pd.DataFrame(listings, columns=["latitude", "longitude", "rentamount"])

    df["rentamount"] = pd.to_numeric(df["rentamount"], errors="coerce")
    df.dropna(inplace=True)

    points = df[["longitude", "latitude"]].values  
    rent_values = df["rentamount"].values 

    vor = Voronoi(points)
    
    polygons = []
    for region in vor.regions:
        if not region or -1 in region:  
            continue
        polygon_coords = [vor.vertices[i] for i in region]
        polygons.append(Polygon(polygon_coords))

    gdf = gpd.GeoDataFrame({"geometry": polygons, "rent": rent_values[:len(polygons)]})
    gdf["rent_scaled"] = gdf["rent"] / gdf["rent"].max()  
    
    geojson = gdf.to_json()

    return JSONResponse(content=geojson)

@app.get("/listing/beds/{n_beds}")
def get_listing_beds(n_beds: int, db: Session = Depends(get_db)):
    """
    Gets listing from database by ID
    """
    if n_beds == 0:
        listings = db.query(HousingListing).all()
    elif n_beds != 5:
        listings = db.query(HousingListing).filter(HousingListing.available_bedrooms==n_beds).all()
    else:
        listings = db.query(HousingListing).filter(HousingListing.available_bedrooms>=n_beds).all()
    if not listings:
        raise HTTPException(status_code=404, detail="Listing not found")
    return [serialize_listing(listing) for listing in listings]

@app.get("/listing/baths/{n_baths}")
def get_listing_baths(n_baths: int, db: Session = Depends(get_db)):
    """
    Gets listing from database by ID
    """
    n_baths = float(n_baths / 2)
    if n_baths == 0:
        listings = db.query(HousingListing).all()
    elif n_baths != 3:
        listings = db.query(HousingListing).filter(HousingListing.available_bathrooms==n_baths).all()
    else:
        listings = db.query(HousingListing).filter(HousingListing.available_bathrooms>=n_baths).all()
    if not listings:
        raise HTTPException(status_code=404, detail="Listing not found")
    return [serialize_listing(listing) for listing in listings]

@app.get("/listing/walks")
def get_listing_walk(db: Session = Depends(get_db)):
    """
    Gets listing from database by ID
    """
    mean_walking_time = db.query(func.avg(HousingListing.walk_time_urishall)).scalar()
    listings = db.query(HousingListing).filter(HousingListing.walk_time_urishall<mean_walking_time).all()
    if not listings:
        raise HTTPException(status_code=404, detail="Listing not found")
    return [serialize_listing(listing) for listing in listings]

@app.get("/listing/transit")
def get_listing_transit(db: Session = Depends(get_db)):
    """
    Gets listing from database by ID
    """
    mean_transit_score = db.query(func.avg(HousingListing.transit_score)).scalar()
    listings = db.query(HousingListing).filter(HousingListing.transit_score>mean_transit_score).all()
    if not listings:
        raise HTTPException(status_code=404, detail="Listing not found")
    return [serialize_listing(listing) for listing in listings]

@app.get("/listing/pets")
def get_listing_pet(db: Session = Depends(get_db)):
    """
    Gets listing from database by ID
    """
    listings = db.query(HousingListing).filter(HousingListing.pets=="Yes").all()
    if not listings:
        raise HTTPException(status_code=404, detail="Listing not found")
    return [serialize_listing(listing) for listing in listings]

@app.get("/room-to-rent-listings/")
def get_top_ten_listings(db: Session = Depends(get_db)):
    """
    Gets top ten listings in Database
    """
    listings = db.query(HousingListing).filter(HousingListing.housingtype=="Room to Rent").all()
    if not listings:
        raise HTTPException(status_code=404, detail="Listing not found")

    return [serialize_listing(listing) for listing in listings] 

@app.get("/rent-listings/")
def get_top_ten_listings(db: Session = Depends(get_db)):
    """
    Gets top ten listings in Database
    """
    listings = db.query(HousingListing).filter(HousingListing.housingtype=="Rent").all()
    if not listings:
        raise HTTPException(status_code=404, detail="Listing not found")

    return [serialize_listing(listing) for listing in listings] 

@app.get("/shared-listings/")
def get_top_ten_listings(db: Session = Depends(get_db)):
    """
    Gets top ten listings in Database
    """
    listings = db.query(HousingListing).filter(HousingListing.housingtype=="Shared").all()
    if not listings:
        raise HTTPException(status_code=404, detail="Listing not found")

    return [serialize_listing(listing) for listing in listings] 

@app.get("/listing/{listing_id}")
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    """
    Gets listing from database by ID
    """
    listing = db.query(HousingListing).filter(HousingListing.listingid==listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return serialize_listing(listing)

"""
SITE SELECTOR
"""
SITE_SELECTOR_PATH = Path(__file__).resolve().parent / "site_selector"

if SITE_SELECTOR_PATH.exists() and str(SITE_SELECTOR_PATH) not in sys.path:
    sys.path.append(str(SITE_SELECTOR_PATH))

import site_selector_api

@app.get("/vacant-lots")
def get_vacant_lots():
    gdf = site_selector_api.load_and_prepare_data()
    gdf = site_selector_api.filter_ithaca_lots(gdf)

    percentile_90 = gdf["RedevelopmentIndex"].quantile(0.9)
    gdf = gdf[
        (gdf["PROPCLASS"] == "Vacant") |
        (gdf["RedevelopmentIndex"] >= percentile_90)
    ]

    gdf = site_selector_api.add_zoning_metadata(gdf)
    gdf = gdf.fillna(np.nan)  
    return JSONResponse(content=site_selector_api.sanitize_for_json(gdf))

@app.get("/all-lots")
def get_all_lots():
    gdf = site_selector_api.load_and_prepare_data()
    gdf = site_selector_api.filter_ithaca_lots(gdf)
    gdf = site_selector_api.add_zoning_metadata(gdf)
    gdf = gdf.fillna(np.nan)  
    return JSONResponse(content=site_selector_api.sanitize_for_json(gdf))

"""
METRICS
Prometheus + Grafana
"""
SSE = Gauge("sse", "Sum of Squared Error")
SSR = Gauge("ssr", "Sum of Squared Residuals")
SST = Gauge("sst", "Sum of Squared Total")
PREDICTION_ERROR = Gauge("prediction_error", "Absolute error between prediction and actual")
COEFFICIENT_OF_DETERMINATION = Gauge("coefficient_of_determination", "Proportion of variation explained by regression model")
ROWS = Gauge("rows", "Proportion of variation explained by regression model")

# instrumentator.add(COEFFICIENT_OF_DETERMINATION)
# instrumentator.add(SSE)
# instrumentator.add(SSR)
# instrumentator.add(SST)
# instrumentator.add(PREDICTION_ERROR)
# instrumentator.add(ROWS)


@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/pipeline-metrics/")
def get_pipeline_metrics(db: Session = Depends(get_db)):
    """
    Fetch pipeline metrics with time series data for mean rent and average Moran's I
    """
    try:
        query = text("""
            SELECT run_timestamp, spatial_patterns, landlord_behavior, overpricing, 
                   model_performance, feature_importance
            FROM rental_model_runs 
            ORDER BY run_timestamp DESC
        """)
        
        results = db.execute(query).fetchall()
        
        if not results:
            return JSONResponse(
                status_code=404,
                content={"error": "No pipeline metrics found"}
            )
        
        def parse_json_column(value):
            if value is None:
                return {}
            elif isinstance(value, dict):
                return value
            elif isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return {}
            else:
                return {}
        
        latest_result = results[0]
        latest_metrics = {
            "spatial_patterns": parse_json_column(latest_result[1]),
            "landlord_behavior": parse_json_column(latest_result[2]),
            "overpricing": parse_json_column(latest_result[3]),
            "model_performance": parse_json_column(latest_result[4]),
            "feature_importance": parse_json_column(latest_result[5])
        }
        
        mean_rent_time_series = []
        moran_i_values = []
        
        for result in results:
            timestamp = result[0]
            spatial_patterns = parse_json_column(result[1])
            
            if spatial_patterns and 'mean_rent' in spatial_patterns:
                mean_rent_time_series.append({
                    'date': timestamp.isoformat(),
                    'mean_rent': spatial_patterns['mean_rent']
                })
            
            if spatial_patterns and 'global_moran' in spatial_patterns and 'I' in spatial_patterns['global_moran']:
                moran_i_values.append(spatial_patterns['global_moran']['I'])
        
        average_moran_i = sum(moran_i_values) / len(moran_i_values) if moran_i_values else 0
        
        latest_metrics["spatial_patterns"]["mean_rent_time_series"] = mean_rent_time_series
        latest_metrics["spatial_patterns"]["average_moran_i"] = average_moran_i
        
        return latest_metrics
        
    except Exception as e:
        logging.error(f"Error fetching pipeline metrics: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to fetch pipeline metrics: {str(e)}"}
        )

def get_sum_of_squares_error(db: Session = Depends(get_db)):
    """
    Sum of squared errors (SSE) in log-space.
    Measures the total squared difference between log(actual) and log(predicted).
    """
    listings = db.query(HousingListing).all()
    squared_residuals = [
        (np.log(float(listing.rent_per_person)) - np.log(float(listing.predictedrent)))**2
        for listing in listings
    ]
    return np.sum(squared_residuals)

def get_sum_of_squares_regression(db: Session = Depends(get_db)):
    """
    Sum of squares due to regression (SSR) in log-space.
    Measures how much of the variance in log(actual) is captured by the predictions.
    """
    listings = db.query(HousingListing).all()
    log_rents = [np.log(float(listing.rent_per_person)) for listing in listings]
    log_preds = [np.log(float(listing.predictedrent)) for listing in listings]
    mean_log_rent = np.mean(log_rents)
    squared_regression_residuals = [(pred - mean_log_rent)**2 for pred in log_preds]
    return np.sum(squared_regression_residuals)

def get_sum_of_squares_total(db: Session = Depends(get_db)):
    """
    Total sum of squares (SST) in log-space.
    Measures the total variance in log(actual).
    """
    listings = db.query(HousingListing).all()
    log_rents = [np.log(float(listing.rent_per_person)) for listing in listings]
    mean_log_rent = np.mean(log_rents)
    total_squared_errors = [(rent - mean_log_rent)**2 for rent in log_rents]
    return np.sum(total_squared_errors)

def get_mse(sse):
    """
    Gets MSE from SSE np.mean(SSE)
    """
    return np.mean(sse)

def get_coefficient_of_determination(sse, sst):
    """
    Gets R^2 from SSR/SST
    """
    return 1-sse/sst

@app.get("/metric-calculations")
def custom_metrics(db: Session = Depends(get_db)):
    sse = get_sum_of_squares_error(db)
    ssr = get_sum_of_squares_regression(db)
    sst = get_sum_of_squares_total(db)
    mse = get_mse(sse)
    r2 = get_coefficient_of_determination(ssr, sst)

    SSE.set(sse)
    SSR.set(ssr)
    SST.set(sst)
    PREDICTION_ERROR.set(mse)
    COEFFICIENT_OF_DETERMINATION.set(r2)
    ROWS.set(db.query(HousingListing).count())

    return {"status": "metrics updated"}

@app.get("/metrics-debug")
def metrics_debug(db: Session = Depends(get_db)):
    sse = get_sum_of_squares_error(db)
    ssr = get_sum_of_squares_regression(db)
    sst = get_sum_of_squares_total(db)
    rows = db.query(HousingListing).all()
    return {
        "sse": sse,
        "ssr": ssr,
        "sst": sst,
        "r_squared": get_coefficient_of_determination(ssr, sst),
        "rows": len(rows)
    }

@app.get("/")
async def root():
    return {"message": "Hello from Arjun!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)