import os
import requests

def geocode_google(query):
    """
    Perform a geocoding search using Google's Geocoding API.

    Args:
        query (str): The search query (e.g., address, location).

    Returns:
        list: A list of places matching the query with address, coordinates, and bounds.
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
    query = f"{row['ListingAddress']}, {row['ListingCity']}, {row['ListingZip']}"
    return geocode_google(query)     

