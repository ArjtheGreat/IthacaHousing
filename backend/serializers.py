"""
Serialization functions for converting database models to JSON-compatible dictionaries
"""
import numpy as np


def safe_float(value):
    """
    Convert value to float, handling inf/nan values
    
    Args:
        value: Any value that should be converted to float
        
    Returns:
        float or None: The converted value, or None if invalid (inf, nan, error)
    """
    if value is None:
        return None
    try:
        float_val = float(value)
        if np.isinf(float_val) or np.isnan(float_val):
            return None
        return float_val
    except (ValueError, TypeError):
        return None


def serialize_listing(listing):
    """
    Convert SQLAlchemy HousingListing model to dict with proper type handling
    
    Args:
        listing: HousingListing database model instance
        
    Returns:
        dict: JSON-serializable dictionary with all listing fields
    """
    return {
        "listingid": int(listing.listingid) if listing.listingid else None,
        "listingaddress": listing.listingaddress,
        "listingcity": listing.listingcity,
        "listingzip": listing.listingzip,
        "shortdescription": listing.shortdescription,
        "rentamount": safe_float(listing.rentamount),
        "renttype": listing.renttype,
        "pets": listing.pets,
        "amenities": listing.amenities,
        "bedrooms": safe_float(listing.bedrooms),
        "bathrooms": safe_float(listing.bathrooms),
        "housingtype": listing.housingtype,
        "latitude": safe_float(listing.latitude),
        "longitude": safe_float(listing.longitude),
        "listingphotos": listing.listingphotos,
        "walk_time": safe_float(listing.walk_time),
        "walk_routes": listing.walk_routes,
        "bike_time": safe_float(listing.bike_time),
        "bike_routes": listing.bike_routes,
        "drive_time": safe_float(listing.drive_time),
        "drive_routes": listing.drive_routes,
        "transit_score": safe_float(listing.transit_score),
        "amenities_score": safe_float(listing.amenities_score),
        "overallsafetyratingpct": safe_float(listing.overallsafetyratingpct),
        "predictedrent": safe_float(listing.predictedrent),
        "differenceinfairvalue": safe_float(listing.differenceinfairvalue),
        "predicted_rent_cma": safe_float(listing.predicted_rent_cma),
        "nearest_neighbor_listingids": listing.nearest_neighbor_listingids,
        "rent_per_person": safe_float(listing.rent_per_person),
        "num_people": safe_float(listing.num_people),
        
    }
