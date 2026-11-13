"""City of Ithaca Business Improvement District (BID) point-in-polygon indicator.

Official source: City of Ithaca GIS, BID feature layer 0.
The City's GIS metadata states the polygon was compiled from paper maps
in the late 1990s and has not been updated: treat edge classifications
as approximate, not authoritative parcel-level determinations.
"""
import json
import urllib.parse
import urllib.request
from functools import lru_cache

import geopandas as gpd
import pandas as pd
from shapely.geometry import shape

BID_LAYER = (
    "https://services5.arcgis.com/R1JbITZvSQHJsl5r/ArcGIS/rest/services/"
    "City_of_Ithaca_OG_Map_Service/FeatureServer/0/query"
)


@lru_cache(maxsize=1)
def load_bid_polygons():
    """Fetch the official polygon once per Python process; do not guess boundaries."""
    query = urllib.parse.urlencode({
        "where": "1=1", "outFields": "OBJECTID", "outSR": "4326",
        "returnGeometry": "true", "f": "geojson",
    })
    request = urllib.request.Request(
        f"{BID_LAYER}?{query}",
        headers={"User-Agent": "IthacaInsights/1.0 (geographic enrichment)"},
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        payload = json.load(response)
    features = payload.get("features", [])
    if payload.get("type") != "FeatureCollection" or not features:
        raise RuntimeError("City of Ithaca BID GIS returned no usable polygons")
    geometries = [shape(f["geometry"]) for f in features if f.get("geometry")]
    if not geometries or any(g.is_empty for g in geometries):
        raise RuntimeError("City of Ithaca BID GIS returned invalid geometry")
    return geometries


def assign_bid(frame: pd.DataFrame) -> pd.DataFrame:
    """Set nullable boolean True/False for valid property coordinates.

    If the authoritative GIS endpoint cannot be reached, *do not* label
    properties False. Raise so the pipeline cannot publish misleading flags.
    """
    out = frame.copy()
    if not {"latitude", "longitude"}.issubset(out.columns):
        raise ValueError("BID enrichment requires latitude and longitude")
    out["in_business_improvement_district"] = pd.Series(
        pd.NA, index=out.index, dtype="boolean"
    )
    lat = pd.to_numeric(out["latitude"], errors="coerce")
    lon = pd.to_numeric(out["longitude"], errors="coerce")
    valid = lat.between(-90, 90) & lon.between(-180, 180)
    if not valid.any():
        return out

    polygons = load_bid_polygons()
    points = gpd.points_from_xy(lon[valid], lat[valid])
    out.loc[valid, "in_business_improvement_district"] = [
        any(polygon.covers(point) for polygon in polygons)
        for point in points
    ]
    print(
        "🏙️ Business Improvement District: "
        f"{int(out['in_business_improvement_district'].fillna(False).sum())} inside, "
        f"{int((out['in_business_improvement_district'] == False).fillna(False).sum())} outside, "
        f"{int(out['in_business_improvement_district'].isna().sum())} unknown"
    )
    return out
