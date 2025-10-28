"""
Serialization functions for converting database models to JSON-compatible dictionaries
"""
import numpy as np
import json
import ast


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


def parse_listing_types(value):
    """
    Parse listing types from various formats to a list
    
    Args:
        value: String representation of a list or already a list
        
    Returns:
        list or None: Parsed list of listing types
    """
    if value is None:
        return None
    
    # If it's already a list, return it
    if isinstance(value, list):
        return value
    
    if not isinstance(value, str):
        return None
    
    # Try to parse as JSON first
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return parsed
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Try to parse as Python list format using ast.literal_eval
    try:
        parsed = ast.literal_eval(value)
        if isinstance(parsed, list):
            return parsed
    except (ValueError, SyntaxError):
        pass
    
    # If parsing fails, return the original value as a single-item list
    return [value] if value else None


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
        "createdate": listing.createdate.isoformat() if listing.createdate else None,
        "shortdescription": listing.shortdescription,
        "rentamount": safe_float(listing.rentamount),
        "renttype": listing.renttype,
        "dateavailable": listing.dateavailable.isoformat() if listing.dateavailable else None,
        "unitnumber": listing.unitnumber,
        "listingtypes": parse_listing_types(listing.listingtypes),
        "listingexpirationdate": listing.listingexpirationdate.isoformat() if listing.listingexpirationdate else None,
        "lengthavailable": safe_float(listing.lengthavailable),
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
        "valid_certificate_of_compliance": listing.valid_certificate_of_compliance,
        "predictedrent": safe_float(listing.predictedrent),
        "differenceinfairvalue": safe_float(listing.differenceinfairvalue),
        "predicted_rent_cma": safe_float(listing.predicted_rent_cma),
        "nearest_neighbor_listingids": listing.nearest_neighbor_listingids,
        "rent_per_person": safe_float(listing.rent_per_person),
        "num_people": safe_float(listing.num_people),
        "total_rent_amount": safe_float(listing.total_rent_amount),
        "owner_name": listing.owner_name,
        "neighborhood": listing.neighborhood,
        "nearest_stop_name": listing.nearest_stop_name,
        "walk_time_to_nearest_stop": safe_float(listing.walk_time_to_nearest_stop),
        "transit_time_to_ag_quad": safe_float(listing.transit_time_to_ag_quad),
        "transit_time_to_arts_quad": safe_float(listing.transit_time_to_arts_quad),
        "transit_time_to_eng_quad": safe_float(listing.transit_time_to_eng_quad),
        "iso15": listing.iso15,
        
        "neighborhood_assessment": listing.neighborhood_assessment,
        "property_depth": safe_float(listing.property_depth),
        "property_frontage": safe_float(listing.property_frontage),
        "property_acres": safe_float(listing.property_acres),
        "property_pc": listing.property_pc,
        "water_access": listing.water_access,
        "sewer_access": listing.sewer_access,
        "sewer_name": listing.sewer_name,
        "year_built": listing.year_built,
        "assessment_sqft": safe_float(listing.assessment_sqft),
        "sale_price": safe_float(listing.sale_price)
    }
