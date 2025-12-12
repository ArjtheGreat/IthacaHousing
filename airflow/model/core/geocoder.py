import os
import requests
import sys

import re

import re

def move_directional_after_number(addr):
    """
    Detects directional suffixes at the end of an address (E, W, N, S, NE, NW, SE, SW)
    and moves them immediately after the street number.
    """
    if not isinstance(addr, str) or not addr.strip():
        return addr
    
    addr = addr.strip()

    # Detect trailing directional
    m = re.search(r"\b(E|W|N|S|NE|NW|SE|SW)$", addr, flags=re.IGNORECASE)
    if not m:
        return addr 

    directional = m.group(1).upper()

    core = re.sub(r"\b(E|W|N|S|NE|NW|SE|SW)$", "", addr, flags=re.IGNORECASE).strip()

    parts = core.split()
    if not parts:
        return addr

    number = parts[0]

    rest = " ".join(parts[1:])

    # Reassemble: num + directional + rest
    return f"{number} {directional} {rest}".strip()


def geocode_google(query):
    """
    Perform a geocoding search using Google's Geocoding API.

    Args:
        query (str): The search query (e.g., address, location).

    Returns:
        dict: A dictionary with lat and lng keys, or error information.
    """
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": query,
        "key": os.getenv("GOOGLE_PLACES_API_KEY")
    }

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data["status"] == "OK":
            for place in data["results"]:
                return place["geometry"]["location"]
        else:
            return {
                "error": data["status"],
                "message": data.get("error_message", "No error message provided"),
            }
    else:
        return {
            "error": "HTTP_ERROR",
            "message": f"HTTP status code: {response.status_code}",
        }

def get_coordinates(row):
    """
    Get coordinates for a listing row, using move_directional_to_front to improve address formatting.
    Returns a dict with 'latitude' and 'longitude' keys (or 'error' key if failed).
    """
    address = row.get('ListingAddress', row.get('listingaddress', ''))
    if address:
        address = move_directional_after_number(address)
    print(f"new address: {address}")
    city = row.get('ListingCity', row.get('listingcity', ''))
    zip_code = row.get('ListingZip', row.get('listingzip', ''))
    
    query = f"{address}, {city}, {zip_code}"
    result = geocode_google(query)
    
    if 'error' in result:
        return result
    else:
        return {
            'latitude': result.get('lat'),
            'longitude': result.get('lng')
        }     

