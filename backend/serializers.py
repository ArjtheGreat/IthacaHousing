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
        "available_bedrooms": safe_float(listing.available_bedrooms),
        "available_bathrooms": safe_float(listing.available_bathrooms),
        "housingtype": listing.housingtype,
        "latitude": safe_float(listing.latitude),
        "longitude": safe_float(listing.longitude),
        "listingphotos": listing.listingphotos,
        "walk_routes": listing.walk_routes,
        "bike_routes": listing.bike_routes,
        "drive_routes": listing.drive_routes,
        "walk_time_urishall": safe_float(listing.walk_time_urishall),
        "walk_time_agriculturequad": safe_float(listing.walk_time_agriculturequad),
        "walk_time_artsquad": safe_float(listing.walk_time_artsquad),
        "walk_time_engineeringquad": safe_float(listing.walk_time_engineeringquad),
        "bike_time_urishall": safe_float(listing.bike_time_urishall),
        "bike_time_agriculturequad": safe_float(listing.bike_time_agriculturequad),
        "bike_time_artsquad": safe_float(listing.bike_time_artsquad),
        "bike_time_engineeringquad": safe_float(listing.bike_time_engineeringquad),
        "drive_time_urishall": safe_float(listing.drive_time_urishall),
        "drive_time_agriculturequad": safe_float(listing.drive_time_agriculturequad),
        "drive_time_artsquad": safe_float(listing.drive_time_artsquad),
        "drive_time_engineeringquad": safe_float(listing.drive_time_engineeringquad),
        "transit_score": safe_float(listing.transit_score),
        "amenities_score": safe_float(listing.amenities_score),
        "overallsafetyratingpct": safe_float(listing.overallsafetyratingpct),
        "predictedrent": safe_float(listing.predictedrent),
        "differenceinfairvalue": safe_float(listing.differenceinfairvalue),
        "predicted_rent_cma": safe_float(listing.predicted_rent_cma),
        "nearest_neighbor_listingids": listing.nearest_neighbor_listingids,
        "rent_per_person": safe_float(listing.rent_per_person),
        "num_people": safe_float(listing.num_people),
        "total_rent_amount": safe_float(listing.total_rent_amount),
    }
