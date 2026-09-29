"""Fetch all Cornell listing floor plans and preprocess for the housing pipeline.

No browser, modal clicks, or per-property requests are needed for the fields here.
Usage: python cornell_listing_scraper.py [--output latest_listings.csv]
       python cornell_listing_scraper.py --html saved_listing.html
"""
from __future__ import annotations

import argparse
import base64
import csv
from html import unescape
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen

URL = "https://offcampus.housing.cornell.edu/listing"
ASSIGNMENT = re.compile(r"\b(?:var|let|const)\s+listingData\s*=\s*JSON\.parse\(JSON\.stringify\(")
COLUMNS = [
    "PropertyId", "ListingAddress", "ListingCity", "ListingZip", "RentType",
    "HousingType", "PropertyCategory", "ShortDescription", "SafetyRatings", "Amenities", "Pets",
    "PropertyHighlights", "name", "address", "walk_time", "phone", "detail_url",
    "ListingId", "FloorplanId", "LegacyListingId", "UnitName", "UnitNumber",
    "ListingGranularity", "RoomStatus", "PropertyUnitsNumber",
    "RentAmount", "RentMin", "RentMax",
    "Bedrooms", "Bathrooms", "SqFt",
    "AvailableFrom", "AvailableDate", "LengthAvailable",
    "latitude", "longitude", "RentRaw",
]


class _Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def plain_description(value):
    if not value:
        return None
    try:
        decoded = base64.b64decode(value, validate=True).decode("utf-8")
    except (ValueError, UnicodeError):
        decoded = str(value)
    parser = _Text()
    parser.feed(decoded)
    return " ".join(unescape(" ".join(parser.parts)).split()) or None


def number(value):
    if value is None or str(value).strip().lower() in {"", "ask", "n/a"}:
        return None
    if str(value).strip().lower() == "studio":
        return 0.0
    match = re.fullmatch(r"\s*\$?\s*([\d,]+(?:\.\d+)?)\s*", str(value))
    return float(match.group(1).replace(",", "")) if match else None


def address_parts(value):
    address = re.sub(r",?\s*(?:USA|United States)\s*$", "", value or "", flags=re.I).strip(" ,")
    match = re.search(r"(?:,\s*|\s+)(Ithaca|Lansing|Dryden|Cayuga Heights|Trumansburg|Freeville|Newfield),\s*[A-Z]{2}\s+(\d{5})(?:-\d{4})?$", address, re.I)
    if match:
        return address[:match.start()].strip(" ,"), match.group(1).strip(), match.group(2)
    match = re.search(r",\s*([^,]+),\s*[A-Z]{2}\s+(\d{5})(?:-\d{4})?$", address)
    if match:
        return address[:match.start()].strip(" ,"), match.group(1).strip(), match.group(2)
    return address, None, None


def extract_listing_data(html):
    match = ASSIGNMENT.search(html)
    if not match:
        raise ValueError("Embedded listingData assignment missing; inspect the new page source")
    # raw_decode stops at the end of the JSON object, regardless of the size of the page.
    data, _ = json.JSONDecoder().raw_decode(html, match.end())
    if not isinstance(data, dict) or not data:
        raise ValueError("Embedded listingData is empty or has an unexpected shape")
    return data


def unique_strings(value):
    if isinstance(value, dict):
        value = [item for group in value.values() for item in (group if isinstance(group, list) else [group])]
    return list(dict.fromkeys(str(item).strip() for item in (value or []) if isinstance(item, str) and item.strip()))


def rows_from_data(data):
    rows = []
    for key, prop in data.items():
        pid = str(prop.get("id") or key)
        address = prop.get("address") or prop.get("campus_address") or ""
        street, city, zip_code = address_parts(address)
        amenities = unique_strings(prop.get("features"))
        if not amenities:
            amenities = unique_strings(prop.get("additional"))
        highlights = prop.get("features") if isinstance(prop.get("features"), dict) else {}
        pet_terms = unique_strings(prop.get("pets"))
        pets = int(bool(prop.get("pets_allowed") or any(
            "allowed" in term.lower() and "not" not in term.lower() for term in pet_terms
        )))
        rent_type = "Price per Person" if prop.get("rent_style") == "person" or prop.get("per_person_property") else "Price Per Unit"
        base = {
            "PropertyId": pid,
            "ListingAddress": street,
            "ListingCity": city,
            "ListingZip": zip_code,
            "RentType": rent_type,
            "HousingType": "Rent",
            "PropertyCategory": prop.get("category_title"),
            "ShortDescription": plain_description(prop.get("description")) or prop.get("title"),
            "SafetyRatings": "{}",
            "Amenities": json.dumps(amenities, ensure_ascii=False),
            "Pets": pets,
            "PropertyHighlights": json.dumps(highlights, ensure_ascii=False),
            "name": prop.get("title"),
            "address": address,
            "walk_time": prop.get("distance_partner") or prop.get("distance"),
            "phone": prop.get("phone") or prop.get("contact_number") or prop.get("lead_text"),
            "detail_url": f"{URL}?property={pid}",
            "latitude": prop.get("lat"),
            "longitude": prop.get("lng"),
        }
        # reformat_floorplans contains the same IDs and adds room_status and
        # unit_number. It is not a second set of listings.
        formatted = {
            str(item["id"]): item
            for group in (prop.get("reformat_floorplans") or {}).values()
            for item in group
            if item.get("id") is not None
        }
        floorplans = prop.get("floorplans") or [None]
        for index, plan in enumerate(floorplans):
            plan = plan or {}
            extra = formatted.get(str(plan.get("id")), {})
            low = number(plan.get("min_rent"))
            high = number(plan.get("max_rent"))
            direct = number(plan.get("rent"))
            # A range has no single exact rent; use its lower bound and retain both.
            rent = low if low is not None else direct
            if high is None and rent is not None:
                high = rent
            rows.append({
                **base,
                # Use the stable source floor-plan ID for database upserts.
                "ListingId": f"{pid}-{plan['id']}" if plan.get("id") is not None else f"{pid}-property",
                "FloorplanId": plan.get("id"),
                "LegacyListingId": f"{pid}-{index}",
                "UnitName": plan.get("title"),
                "UnitNumber": extra.get("unit_number"),
                "ListingGranularity": "floorplan" if plan else "property",
                "RoomStatus": extra.get("room_status"),
                "PropertyUnitsNumber": prop.get("units_number"),
                "RentAmount": rent,
                "RentMin": low if low is not None else rent,
                "RentMax": high,
                "Bedrooms": number(plan.get("bed")) if plan else number(prop.get("min_bed")),
                "Bathrooms": number(plan.get("bath")) if plan else number(prop.get("min_bath")),
                "SqFt": number(plan.get("sq_footage")),
                # Site "Available" field (Now / 08-01-2027) — not lease length.
                "AvailableFrom": plan.get("available_date") or prop.get("available"),
                "AvailableDate": plan.get("available_date"),
                # Compat stub only; listing page has no lease-term field.
                "LengthAvailable": None,
                "RentRaw": plan.get("rent"),
            })
    return rows


def fetch_html():
    request = Request(URL, headers={"User-Agent": "Mozilla/5.0 (compatible; CornellListingResearch/1.0)"})
    with urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")


def scrape_all_listings(html=None):
    """Drop-in replacement for the old async browser scraper (now synchronous)."""
    return rows_from_data(extract_listing_data(html if html is not None else fetch_html()))


def fetch_active_listings():
    """Fetch all listed floor plans and write CSV plus the raw JSON dump."""
    import pandas as pd
    frame = pd.DataFrame(scrape_all_listings(), columns=COLUMNS)
    data_path = get_writable_data_path()
    frame.to_csv(data_path, index=False)
    raw_path = get_scraped_raw_path()
    with open(raw_path, "w", encoding="utf-8") as file:
        json.dump(frame.where(pd.notna(frame), None).to_dict("records"), file, ensure_ascii=False, default=str)
    print(f"Wrote {len(frame)} floor-plan rows to {data_path} and {raw_path}")
    return frame


def _base_dir():
    for path in ("/opt/airflow/model", "/usr/local/airflow/model"):
        if os.path.isdir(path):
            return Path(path)
    return Path(__file__).resolve().parent


def get_writable_data_path():
    for path in (_base_dir() / "latest_listings.csv", Path("/tmp/latest_listings.csv")):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.with_suffix(".write_test").open("w"):
                pass
            path.with_suffix(".write_test").unlink()
            return path
        except OSError:
            continue
    raise OSError("No writable path for latest_listings.csv")


def get_scraped_raw_path():
    path = _base_dir() / "core" / "scraped_properties_raw.json"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.with_suffix(".write_test").open("w"):
            pass
        path.with_suffix(".write_test").unlink()
        return path
    except OSError:
        return Path("/tmp/scraped_properties_raw.json")


def get_geojson_path():
    candidates = (
        _base_dir() / "data" / "cugir-008030-geojson.json",
        _base_dir() / "cugir-008030-geojson.json",
        Path("/content/cugir-008030-geojson.json"),
        Path("data/cugir-008030-geojson.json"),
    )
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("Ithaca boundary GeoJSON not found")


def housing_data_preprocessing(existing_coordinates=None):
    """Keep every Ithaca floor plan; reuse source coordinates, filling gaps once per property."""
    import geopandas as gpd
    import numpy as np
    import pandas as pd

    df = pd.read_csv(get_writable_data_path(), dtype={"ListingId": str, "PropertyId": str})
    for col in ("latitude", "longitude"):
        df[col] = pd.to_numeric(df[col], errors="coerce") if col in df else np.nan

    if existing_coordinates is not None and not existing_coordinates.empty:
        existing = existing_coordinates.copy()
        existing["listingid"] = existing["listingid"].astype(str)
        for col in ("latitude", "longitude"):
            existing[col] = pd.to_numeric(existing[col], errors="coerce")
        by_listing = existing.dropna(subset=["latitude", "longitude"]).drop_duplicates("listingid").set_index("listingid")
        # The old pipeline used IDs such as property-0; reuse their coordinates
        # by property when the new stable floor-plan ID has no exact match.
        existing["property_key"] = existing["listingid"].str.replace(r"-\d+$", "", regex=True)
        by_property = existing.dropna(subset=["latitude", "longitude"]).drop_duplicates("property_key").set_index("property_key")
        missing = df[["latitude", "longitude"]].isna().any(axis=1)
        for idx in df.index[missing]:
            key, pid = df.at[idx, "ListingId"], df.at[idx, "PropertyId"]
            source = by_listing.loc[key] if key in by_listing.index else by_property.loc[pid] if pid in by_property.index else None
            if source is not None:
                df.at[idx, "latitude"] = source["latitude"]
                df.at[idx, "longitude"] = source["longitude"]

    if df[["latitude", "longitude"]].isna().any(axis=1).any():
        import sys
        model_path = str(_base_dir())
        if model_path not in sys.path:
            sys.path.insert(0, model_path)
        from core import geocoder

        df["_address_key"] = (
            df.get("ListingAddress", df.get("address", ""))
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
            + "|"
            + df.get("ListingCity", pd.Series("", index=df.index))
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
            + "|"
            + df.get("ListingZip", pd.Series("", index=df.index))
            .fillna("")
            .astype(str)
            .str.strip()
        )

        missing_mask = df[["latitude", "longitude"]].isna().any(axis=1)
        unique_keys = df.loc[missing_mask, "_address_key"].drop_duplicates()
        print(
            f"🌍 Geocoding {len(unique_keys)} unique addresses "
            f"(for {int(missing_mask.sum())} unit rows)..."
        )

        cache = {}
        for key in unique_keys:
            sample_idx = df.index[df["_address_key"] == key][0]
            result = geocoder.get_coordinates(df.loc[sample_idx])
            if isinstance(result, dict) and "error" not in result:
                cache[key] = (
                    result.get("latitude", result.get("lat", np.nan)),
                    result.get("longitude", result.get("lng", np.nan)),
                )
            else:
                cache[key] = (np.nan, np.nan)

        for idx in df.index[missing_mask]:
            lat, lng = cache[df.at[idx, "_address_key"]]
            df.at[idx, "latitude"] = lat
            df.at[idx, "longitude"] = lng

        df.drop(columns=["_address_key"], inplace=True)

    df["GmapLatitude"] = df["latitude"]
    df["GmapLongitude"] = df["longitude"]
    boundaries = gpd.read_file(get_geojson_path())
    boundaries = boundaries[boundaries["fullname"].isin(["CITY OF ITHACA", "TOWN OF ITHACA"])]
    if boundaries.crs is None:
        raise ValueError("Ithaca boundary GeoJSON has no CRS")
    points = gpd.GeoDataFrame(
        df.dropna(subset=["latitude", "longitude"]).copy(),
        geometry=gpd.points_from_xy(
            df.dropna(subset=["latitude", "longitude"])["longitude"],
            df.dropna(subset=["latitude", "longitude"])["latitude"],
        ),
        crs="EPSG:4326",
    )
    matches = gpd.sjoin(points.to_crs(boundaries.crs), boundaries[["geometry"]], predicate="within", how="inner")
    result = df.loc[matches.index.unique()].copy()
    result["Bedrooms"] = pd.to_numeric(result["Bedrooms"], errors="coerce")
    # Preserve the historical downstream convention: studio contributes 1 to rent math.
    result.loc[result["Bedrooms"] == 0, "Bedrooms"] = 1
    result["Bathrooms"] = pd.to_numeric(result["Bathrooms"], errors="coerce").fillna(1)
    result["RentAmount"] = pd.to_numeric(result["RentAmount"], errors="coerce")
    return result.reset_index(drop=True)

