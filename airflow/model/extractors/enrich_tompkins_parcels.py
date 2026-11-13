"""Enrich rental properties from Tompkins County's 2026 public parcel polygons.

Source:
https://services.arcgis.com/oJbAAWNInLrxvF0A/ArcGIS/rest/services/Parcels_Public/FeatureServer/0

The source is tax-PARCEL data, not a reliable unit-level building inventory.
Only use attributes to fill missing assessment data; preserve existing known
values and report conflicting construction years for manual review.

Download is scoped to the geographic bounding box of current rental listings,
paginated by OBJECTID, and cached as an auditable GeoJSON snapshot.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests

PARCEL_API = (
    "https://services.arcgis.com/oJbAAWNInLrxvF0A/ArcGIS/rest/services/"
    "Parcels_Public/FeatureServer/0/query"
)
SOURCE_YEAR = 2026
SOURCE_NAME = "tompkins_2026_parcel"
# Keep runtime snapshots outside the source checkout (often mounted read-only in
# Docker). Set TOMPKINS_PARCEL_CACHE_DIR to a persistent mounted directory.
CACHE_DIR = Path(os.getenv("TOMPKINS_PARCEL_CACHE_DIR", "/tmp/ithaca_insights_parcels"))
PAGE_SIZE = 50  # Keep polygon responses small for the county ArcGIS gateway

PARCEL_FIELDS = (
    "FID", "PRINTKEY", "LOC", "LOCATION", "LOCADDR", "YEARBUILT",
    "SQ_FT", "SALE_PRICE", "ACRES", "FRONTAGE", "DEPTH",
    "PC", "WATER", "SEWER", "SWRESNAME", "ASMT", "LAND",
    "STORIES", "ZONING", "PROPCLASS",
)

# County fields are parcel-level. SQ_FT is never used as floorplan/unit_sqft.
FIELDS_TO_FILL = {
    "YEARBUILT": "year_built",
    "SQ_FT": "assessment_sqft",
    "SALE_PRICE": "sale_price",
    "ACRES": "property_acres",
    "FRONTAGE": "property_frontage",
    "DEPTH": "property_depth",
    "PC": "property_pc",
    "WATER": "water_access",
    "SEWER": "sewer_access",
    "SWRESNAME": "sewer_name",
    "ASMT": "assessment_total_value",
    "LAND": "assessment_land_value",
    "STORIES": "assessment_stories",
    "ZONING": "assessment_zoning",
    "PROPCLASS": "assessment_property_class",
}
NUMERIC_FIELDS = {
    "year_built", "assessment_sqft", "sale_price", "property_acres",
    "property_frontage", "property_depth", "assessment_total_value",
    "assessment_land_value", "assessment_stories",
}


def _request_json(session: requests.Session, params: dict) -> dict:
    """Query ArcGIS with POST to avoid its reverse proxy's long-URL 404s.

    The county object-ID list can be thousands of characters long even for
    ~250 parcels. GET puts that list into the URL and the gateway returns 404
    before ArcGIS evaluates the request. For small requests GET remains a
    fallback if a proxy disallows POST.
    """
    use_post = "objectIds" in params
    for attempt in range(3):
        try:
            if use_post:
                response = session.post(
                    PARCEL_API, data=params, timeout=(12, 90),
                )
                if response.status_code in (403, 405):
                    # Small 50-ID GET fallback for proxy configurations that
                    # disallow POST. Never retry long URLs.
                    response = session.get(
                        PARCEL_API, params=params, timeout=(12, 90),
                    )
            else:
                response = session.get(
                    PARCEL_API, params=params, timeout=(12, 90),
                )
            response.raise_for_status()
            payload = response.json()
            if "error" in payload:
                raise RuntimeError(f"Tompkins ArcGIS error: {payload['error']}")
            return payload
        except (requests.RequestException, ValueError) as exc:
            if attempt == 2:
                # Report a short actionable error, rather than logging
                # thousands of object IDs as part of the failed URL.
                raise RuntimeError(
                    f"Tompkins ArcGIS query failed (method={'POST' if use_post else 'GET'}, "
                    f"id_count={len(params.get('objectIds', '').split(',')) if use_post else 'n/a'}, "
                    f"status={getattr(getattr(exc, 'response', None), 'status_code', 'unknown')})"
                ) from exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError("Unreachable parcel request")


def _bbox_for_points(lat: pd.Series, lon: pd.Series) -> tuple[float, ...]:
    """Small buffer around all valid rental locations; deterministic snapshot."""
    pad = 0.002
    return (
        round(float(lon.min()) - pad, 5),
        round(float(lat.min()) - pad, 5),
        round(float(lon.max()) + pad, 5),
        round(float(lat.max()) + pad, 5),
    )


def download_parcels_for_bbox(
    bbox: tuple[float, float, float, float],
    cache_dir: str | Path | None = None,
    refresh: bool = False,
    session: requests.Session | None = None,
) -> Path:
    """Download *relevant* county parcels to local GeoJSON, with pagination.

    We do not download the whole county on every daily pipeline run. The
    query envelope covers the listing coordinates; returned polygons are
    county-authored and can extend beyond the envelope. The cached file is
    never accepted for an unrelated bounding box.
    """
    key = hashlib.sha256(json.dumps([SOURCE_YEAR, *bbox]).encode()).hexdigest()[:16]
    target_dir = Path(cache_dir) if cache_dir is not None else CACHE_DIR
    target = target_dir / f"tompkins_parcels_{SOURCE_YEAR}_{key}.geojson"
    if target.is_file() and not refresh:
        return target

    own_session = session is None
    session = session or requests.Session()
    spatial_query = {
        "where": "1=1",
        "geometry": ",".join(map(str, bbox)),
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
    }
    try:
        index = _request_json(session, {
            **spatial_query, "returnIdsOnly": "true", "f": "json",
        })
        ids = sorted(set(index.get("objectIds") or []))
        if not ids:
            raise RuntimeError("County parcel query returned no object IDs")
        features = []
        for start in range(0, len(ids), PAGE_SIZE):
            batch = ids[start:start + PAGE_SIZE]
            data = _request_json(session, {
                "objectIds": ",".join(map(str, batch)),
                "outFields": ",".join(PARCEL_FIELDS),
                "returnGeometry": "true",
                "outSR": "4326",
                "f": "geojson",
            })
            page = data.get("features", [])
            if data.get("type") != "FeatureCollection" or len(page) != len(batch):
                raise RuntimeError(
                    f"Partial/invalid county GeoJSON page at {start}: "
                    f"wanted {len(batch)}, received {len(page)}"
                )
            features.extend(page)
        if len(features) != len(ids):
            raise RuntimeError("Incomplete county parcel download")
        target_dir.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(".geojson.tmp")
        with tmp.open("w", encoding="utf-8") as handle:
            json.dump({
                "type": "FeatureCollection",
                "name": f"Tompkins County parcels tax year {SOURCE_YEAR}",
                "source": PARCEL_API,
                "query_bbox_epsg4326": list(bbox),
                "features": features,
            }, handle, separators=(",", ":"))
        os.replace(tmp, target)
        print(f"🗺️ Downloaded {len(features)} county parcel polygons to {target}")
        return target
    finally:
        if own_session:
            session.close()


def _year(value):
    try:
        val = int(float(value))
    except (ValueError, TypeError):
        return None
    if 1750 <= val <= SOURCE_YEAR:
        return val
    return None


def _positive_number(value):
    try:
        num = float(value)
    except (ValueError, TypeError):
        return None
    return num if 0 < num < float("inf") else None


def _clean_value(raw, field):
    if field == "year_built":
        return _year(raw)
    if field in NUMERIC_FIELDS:
        return _positive_number(raw)
    if raw is None or pd.isna(raw):
        return None
    value = str(raw).strip()
    return value if value and value.lower() not in {"nan", "none", "null"} else None


def _has_value(value):
    if value is None:
        return False
    try:
        if pd.isna(value):
            return False
    except (TypeError, ValueError):
        pass
    return bool(str(value).strip())


def _normalized_address(value) -> str:
    """Basic normalized-address confidence check, not a fallback geocoder."""
    if not _has_value(value):
        return ""
    s = re.sub(r"[^A-Z0-9 ]", " ", str(value).upper())
    s = re.sub(r"\b(AVENUE|AVE)\b", "AVE", s)
    s = re.sub(r"\b(STREET|ST)\b", "ST", s)
    s = re.sub(r"\b(ROAD|RD)\b", "RD", s)
    s = re.sub(r"\b(LANE|LN)\b", "LN", s)
    s = re.sub(r"\b(BOULEVARD|BLVD)\b", "BLVD", s)
    s = re.sub(r"\b(PLACE|PL)\b", "PL", s)
    s = re.sub(r"\b(DRIVE|DR)\b", "DR", s)
    s = re.sub(r"\b(APT|APARTMENT|UNIT|SUITE|STE|FLOOR|FL)\b.*", "", s)
    return " ".join(s.split())


def _county_address(row) -> str:
    """Prefer parcel situs address, not the owner's mailing address."""
    address = row.get("LOCADDR")
    if _has_value(address):
        return str(address)
    return f"{row.get('LOC') or ''} {row.get('LOCATION') or ''}".strip()


def enrich_from_2026_parcels(
    frame: pd.DataFrame,
    cache_dir: str | Path | None = None,
    refresh: bool = False,
) -> pd.DataFrame:
    """Spatially match current listings and fill missing county parcel data.

    Existing valid year_built and assessment fields win on disagreements.
    Never fabricate a year from build style or nearby parcels. Ambiguous
    multi-parcel intersections are skipped unless one address verifies.
    """
    out = frame.copy().reset_index(drop=True)
    for field in FIELDS_TO_FILL.values():
        if field not in out:
            out[field] = pd.NA
    for col in ("parcel_printkey", "parcel_match_method", "year_built_source"):
        if col not in out:
            out[col] = None

    if not {"latitude", "longitude"}.issubset(out.columns):
        raise ValueError("County parcel enrichment requires latitude/longitude")
    lat = pd.to_numeric(out["latitude"], errors="coerce")
    lon = pd.to_numeric(out["longitude"], errors="coerce")
    # Remove obviously invalid/out-of-region coordinates before bounding the
    # county download. Listings outside the county remain unmatched.
    valid = lat.between(42.15, 42.70) & lon.between(-76.90, -76.10)

    existing_year = pd.to_numeric(out["year_built"], errors="coerce")
    if "year_built_source" in out:
        mask = existing_year.between(1750, SOURCE_YEAR) & out["year_built_source"].isna()
        out.loc[mask, "year_built_source"] = "legacy_assessment_csv"

    if not valid.any():
        return out
    snapshot = download_parcels_for_bbox(
        _bbox_for_points(lat[valid], lon[valid]),
        cache_dir=cache_dir,
        refresh=refresh,
    )
    parcels = gpd.read_file(snapshot)
    if parcels.crs is None:
        # GeoJSON is RFC 7946 longitude/latitude, unless explicitly stated.
        parcels = parcels.set_crs("EPSG:4326")
    else:
        parcels = parcels.to_crs("EPSG:4326")
    if "PRINTKEY" not in parcels or "YEARBUILT" not in parcels:
        raise ValueError("County GeoJSON lacks required PRINTKEY/YEARBUILT")
    parcels = parcels.loc[parcels.geometry.notna()].copy()
    parcels = parcels.loc[~parcels.geometry.is_empty]
    if parcels.empty:
        raise ValueError("County GeoJSON had no valid polygon geometries")

    parcels["_parcel_area"] = parcels.to_crs("EPSG:32618").geometry.area
    points = gpd.GeoDataFrame(
        {"_row": out.index[valid]},
        geometry=gpd.points_from_xy(lon[valid], lat[valid]),
        crs="EPSG:4326",
    )
    hits = gpd.sjoin(
        points, parcels, how="inner", predicate="intersects",
    ).reset_index(drop=True)
    if hits.empty:
        print("⚠️ County parcel polygons matched no listing coordinates")
        return out

    addr_col = "ListingAddress" if "ListingAddress" in out else "listingaddress"
    conflicts = 0
    filled_year = 0
    matched_properties = 0
    ambiguous = 0
    for row_id, group in hits.groupby("_row", sort=False):
        current = _normalized_address(out.at[row_id, addr_col]) if addr_col in out else ""
        group = group.copy()
        group["_address_matches"] = group.apply(
            lambda x: bool(current) and
            _normalized_address(_county_address(x)) == current,
            axis=1,
        )
        verified = group[group["_address_matches"]]
        if len(verified) == 1:
            chosen = verified.iloc[0]
            method = "polygon_and_address"
        elif len(group) == 1:
            chosen = group.iloc[0]
            method = "polygon_only"
        else:
            # Multiple overlapping tax parcels: do not guess a winner.
            ambiguous += 1
            continue

        out.at[row_id, "parcel_printkey"] = str(chosen["PRINTKEY"])
        out.at[row_id, "parcel_match_method"] = method
        matched_properties += 1
        for county_field, target_field in FIELDS_TO_FILL.items():
            value = _clean_value(chosen.get(county_field), target_field)
            if value is None:
                continue
            previous = out.at[row_id, target_field]
            if target_field == "year_built" and _has_value(previous):
                prior_year = _year(previous)
                if prior_year is not None and prior_year != value:
                    conflicts += 1
            if not _has_value(previous):
                out.at[row_id, target_field] = value
                if target_field == "year_built":
                    out.at[row_id, "year_built_source"] = SOURCE_NAME
                    filled_year += 1

    print(
        f"🏗️ County 2026 parcel enrichment: {matched_properties}/{len(out)} "
        f"property rows matched; {filled_year} new construction years; "
        f"{ambiguous} ambiguous parcels; {conflicts} conflicting known years "
        "(retained original values)"
    )
    return out
