import asyncio
import pandas as pd
import numpy as np
import time
import sys
import os
from pathlib import Path

MODEL_PATH = "/opt/airflow/model"
if not os.path.exists(MODEL_PATH):
    MODEL_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if MODEL_PATH not in sys.path:
    sys.path.insert(0, MODEL_PATH)

import core.geocoder as geocoder
import ast
import json
import os
import geopandas as gpd
from shapely.geometry import Point


if os.path.exists("/opt/airflow/model"):
    BASE_DIR = "/opt/airflow/model"  
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_writable_data_path():
    """Get a writable path for the data file, trying multiple locations"""
    possible_paths = [
        "/tmp/latest_listings.csv",
        os.path.join(BASE_DIR, "latest_listings.csv"), 
        "./latest_listings.csv", 
    ]
    
    for path in possible_paths:
        try:
            test_file = path + ".test"
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            return path
        except (PermissionError, OSError):
            continue
    
    return "/tmp/latest_listings.csv"

DATA_PATH = get_writable_data_path()
print(f"📁 Using data path: {DATA_PATH}")

def get_geojson_path():
    """Get the path to the GeoJSON file, trying multiple locations"""
    possible_paths = [
        os.path.join(BASE_DIR, "data", "cugir-008030-geojson.json"),
        os.path.join(BASE_DIR, "cugir-008030-geojson.json"),
        "/content/cugir-008030-geojson.json",
        "./data/cugir-008030-geojson.json",
        "./cugir-008030-geojson.json",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return os.path.join(BASE_DIR, "data", "cugir-008030-geojson.json")

GEOJSON_PATH = get_geojson_path()
print(f"🗺️ Using GeoJSON path: {GEOJSON_PATH}")

def fetch_active_listings():
    """Fetches Active Listings by scraping Cornell Off-Campus Housing site"""
    data = asyncio.run(scrape_all_listings())
    housing_data_df = pd.DataFrame(data)
    housing_data_df.to_csv(DATA_PATH, index=False)
    return housing_data_df


def housing_data_preprocessing(existing_coordinates=None):
    """
    Preprocesses House Data (extracts Lat, Lng)
    
    Args:
        existing_coordinates: Optional DataFrame with listingid, latitude, longitude
                             to avoid re-geocoding existing listings
    """
    housing_data_df = pd.read_csv(DATA_PATH)
    
    housing_data_df['latitude'] = np.nan
    housing_data_df['longitude'] = np.nan
    
    if existing_coordinates is not None and not existing_coordinates.empty:
        existing_coordinates['listingid'] = existing_coordinates['listingid'].astype(str)
        
        id_col = None
        if 'ListingId' in housing_data_df.columns:
            id_col = 'ListingId'
        elif 'listingid' in housing_data_df.columns:
            id_col = 'listingid'
        
        if id_col:
            housing_data_df[id_col] = housing_data_df[id_col].astype(str)
            
            existing_coordinates['latitude'] = pd.to_numeric(existing_coordinates['latitude'], errors='coerce')
            existing_coordinates['longitude'] = pd.to_numeric(existing_coordinates['longitude'], errors='coerce')
            
            coords_map = existing_coordinates.set_index('listingid')[['latitude', 'longitude']].to_dict('index')
            
            for idx, row in housing_data_df.iterrows():
                listing_id = str(row[id_col])
                if listing_id in coords_map:
                    housing_data_df.at[idx, 'latitude'] = coords_map[listing_id]['latitude']
                    housing_data_df.at[idx, 'longitude'] = coords_map[listing_id]['longitude']
            
            existing_count = housing_data_df[['latitude', 'longitude']].notna().all(axis=1).sum()
            print(f"📍 Reused coordinates for {existing_count} existing listings")
        else:
            print("⚠️ Could not find ListingId or listingid column in housing_data_df")
    
    listings_to_geocode = housing_data_df[housing_data_df[['latitude', 'longitude']].isna().any(axis=1)]
    print(f"🌍 Geocoding {len(listings_to_geocode)} new listings...")
    
    if len(listings_to_geocode) > 0:
        listings_to_geocode[['latitude', 'longitude']] = listings_to_geocode.apply(
            lambda row: pd.Series(geocoder.get_coordinates(row)), axis=1
        )
        housing_data_df.loc[listings_to_geocode.index, 'latitude'] = listings_to_geocode['latitude']
        housing_data_df.loc[listings_to_geocode.index, 'longitude'] = listings_to_geocode['longitude']
    
    housing_data_df.replace({"latitude": "", "longitude": "", "None": np.nan}, inplace=True)
    
    # Convert latitude and longitude to numeric (float) to avoid isnan errors
    housing_data_df['latitude'] = pd.to_numeric(housing_data_df['latitude'], errors='coerce')
    housing_data_df['longitude'] = pd.to_numeric(housing_data_df['longitude'], errors='coerce')

    boundaries = gpd.read_file(GEOJSON_PATH)

    ithaca_bounds = boundaries[
        boundaries['fullname'].isin(['CITY OF ITHACA', 'TOWN OF ITHACA'])
    ].copy()

    apartments_for_rent = housing_data_df.dropna(subset=["latitude", "longitude"])

    apartments_for_rent_gdf = gpd.GeoDataFrame(
        apartments_for_rent,
        geometry=gpd.points_from_xy(apartments_for_rent.longitude, apartments_for_rent.latitude),
        crs="EPSG:4326"
    )

    apartments_for_rent_bounded = gpd.sjoin(apartments_for_rent_gdf, ithaca_bounds, predicate='within', how='inner')
    apartments_for_rent_bounded = apartments_for_rent_bounded.reset_index(drop=True)
    
    apartments_for_rent = apartments_for_rent_bounded.drop(columns=['geometry', 'index_right', 'index_left'], errors='ignore')

    apartments_for_rent["Bedrooms"] = (
        apartments_for_rent["Bedrooms"]
        .replace("studio", 1)
        .apply(pd.to_numeric, errors="coerce")
    )
    apartments_for_rent["RentAmount"] = pd.to_numeric(apartments_for_rent["RentAmount"], errors="coerce")
    apartments_for_rent["Bedrooms"] = pd.to_numeric(apartments_for_rent["Bedrooms"], errors="coerce")
    apartments_for_rent["Bathrooms"] = pd.to_numeric(apartments_for_rent["Bathrooms"], errors='coerce')

    apartments_for_rent.loc[apartments_for_rent["ListingId"] == 4703, "RentType"] = "Price per Person"
    
    print(apartments_for_rent.head())
    return apartments_for_rent


# @title Scraping for Ithaca
import re
from playwright.async_api import async_playwright


URL = "https://offcampus.housing.cornell.edu/listing"


def clean_text(text):
    if not text:
        return None

    return " ".join(
        text.replace("\xa0", " ").split()
    )


def parse_address(raw_addr):
    """
    Example:
    210 East Green Street, Ithaca, NY 14850

    ->
    address_line: 210 East Green Street
    city_state_zip: Ithaca, NY 14850
    """

    if not raw_addr:
        return None, None

    raw_addr = clean_text(raw_addr)

    match = re.search(
        r"(.+?),\s*([A-Za-z .'-]+,\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?)$",
        raw_addr
    )

    if match:
        return (
            match.group(1).strip(),
            match.group(2).strip()
        )

    return raw_addr, None


async def get_text(locator):
    """
    Safely get text from a locator.
    """
    try:
        if await locator.count() == 0:
            return None

        return clean_text(
            await locator.first.inner_text()
        )
    except:
        return None


async def scrape_all_listings():

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage"
            ]
        )

        page = await browser.new_page(
            viewport={
                "width": 1440,
                "height": 1200
            }
        )

        print("🌐 Loading Cornell housing site...")

        await page.goto(
            URL,
            wait_until="domcontentloaded",
            timeout=60000
        )

        # Wait until listings actually render
        await page.wait_for_selector(
            "li.c-list[data-property-id]",
            timeout=30000
        )

        # --------------------------------------------------
        # Cookie / disclaimer popup
        # --------------------------------------------------

        understand_button = page.locator(
            '[aria-label="I understand"]'
        )

        try:
            if await understand_button.count() > 0:
                if await understand_button.first.is_visible():
                    print("🍪 Closing disclaimer...")
                    await understand_button.first.click()
        except:
            pass

        # --------------------------------------------------
        # LOAD ALL LISTINGS
        # --------------------------------------------------

        previous_count = 0

        while True:

            cards = page.locator(
                "li.c-list[data-property-id]"
            )

            current_count = await cards.count()

            print(
                f"📦 Listings currently loaded: {current_count}"
            )

            load_more = page.locator(
                'button[aria-label="load more"]'
            )

            # No load more button -> done
            if await load_more.count() == 0:
                print("✅ No load-more button remains.")
                break

            try:
                visible = await load_more.first.is_visible()
            except:
                visible = False

            if not visible:
                print("✅ Load-more button hidden.")
                break

            # Prevent infinite loop if the site stops adding results
            if (
                current_count == previous_count
                and previous_count != 0
            ):
                print(
                    "⚠️ Listing count did not increase. Stopping."
                )
                break

            previous_count = current_count

            print("⚡ Loading more listings...")

            await load_more.first.scroll_into_view_if_needed()

            await load_more.first.click()

            # Rather than sleeping blindly, wait until
            # the number of cards increases.
            try:
                await page.wait_for_function(
                    """
                    previousCount => {
                        return document.querySelectorAll(
                            'li.c-list[data-property-id]'
                        ).length > previousCount
                    }
                    """,
                    arg=current_count,
                    timeout=10000
                )

            except:
                # Sometimes final click removes button
                await page.wait_for_timeout(1500)

        # --------------------------------------------------
        # SCRAPE CARDS
        # --------------------------------------------------

        cards = page.locator(
            "li.c-list[data-property-id]"
        )

        count = await cards.count()

        print(f"\n🏠 Total listings found: {count}\n")

        results = []

        for i in range(count):

            card = cards.nth(i)

            property_id = await card.get_attribute(
                "data-property-id"
            )

            print(
                f"🔍 Scraping {i + 1}/{count} "
                f"(property {property_id})"
            )

            # ---------------------------
            # Name
            # ---------------------------

            name = await get_text(
                card.locator(".tmlpCard__title")
            )

            # ---------------------------
            # Address
            # ---------------------------

            raw_address = await get_text(
                card.locator(".tmlpCard__address")
            )

            address_line, city_state_zip = (
                parse_address(raw_address)
            )

            # ---------------------------
            # Availability
            # ---------------------------

            availability = await get_text(
                card.locator(".tmlpCard__availability")
            )

            if availability:
                availability = re.sub(
                    r"^Available:\s*",
                    "",
                    availability,
                    flags=re.I
                )

            # ---------------------------
            # Price
            # ---------------------------

            price = await get_text(
                card.locator(".tmlpCard__priceLine")
            )

            # Remove "/mo" from normalized price
            if price:
                price = re.sub(
                    r"\s*/\s*mo\s*$",
                    "",
                    price,
                    flags=re.I
                ).strip()

            # ---------------------------
            # Beds
            # ---------------------------

            beds = await get_text(
                card.locator(".tmlpCard__bedBadge")
            )

            # ---------------------------
            # Walk time
            # ---------------------------

            walk_time = await get_text(
                card.locator(
                    ".tmlpCard__walk strong"
                )
            )

            # ---------------------------
            # Phone
            # ---------------------------

            phone = None

            phone_buttons = card.locator(
                ".tmlpCard__actions "
                "button.tmlpCard__action--secondary"
            )

            if await phone_buttons.count() > 0:
                phone = await get_text(
                    phone_buttons.first
                )

            results.append({
                "property_id": property_id,
                "name": name,

                "address": raw_address,
                "address_line": address_line,
                "city_state_zip": city_state_zip,

                "availability": availability,
                "price": price,
                "beds": beds,

                "walk_time": walk_time,
                "phone": phone,

                # Very useful if you later open details
                "detail_url": (
                    f"{URL}?property={property_id}"
                    if property_id
                    else None
                )
            })

        await browser.close()

        return results