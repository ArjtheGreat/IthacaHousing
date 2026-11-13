"""Download the 2026 Tompkins County parcel polygons around current listings.

Usage in the Airflow container:
  python /opt/airflow/model/download_tompkins_parcels.py

Or a specific envelope (xmin ymin xmax ymax, EPSG:4326):
  python /opt/airflow/model/download_tompkins_parcels.py --bbox -76.54 42.41 -76.45 42.49

The result is a cached GeoJSON snapshot under model/data/parcel_cache.
Full model ingestion also performs this download automatically on first use.
"""
import argparse
import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from extractors.enrich_tompkins_parcels import (
    _bbox_for_points, download_parcels_for_bbox,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bbox", type=float, nargs=4,
        metavar=("MIN_LON", "MIN_LAT", "MAX_LON", "MAX_LAT"),
        help="Optional override for a WGS84 geographic envelope",
    )
    parser.add_argument(
        "--refresh", action="store_true",
        help="Redownload the snapshot even when a matching cache exists",
    )
    args = parser.parse_args()
    if args.bbox:
        bbox = tuple(args.bbox)
    else:
        if not os.getenv("DB_URI"):
            parser.error("DB_URI is required unless --bbox is supplied")
        engine = create_engine(os.environ["DB_URI"])
        try:
            with engine.connect() as conn:
                frame = pd.read_sql(
                    text("SELECT latitude, longitude FROM housing_listings"),
                    conn,
                )
        finally:
            engine.dispose()
        lat = pd.to_numeric(frame["latitude"], errors="coerce")
        lon = pd.to_numeric(frame["longitude"], errors="coerce")
        valid = lat.between(42.15, 42.70) & lon.between(-76.90, -76.10)
        if not valid.any():
            parser.error("No valid Tompkins County coordinates found in DB")
        bbox = _bbox_for_points(lat[valid], lon[valid])

    if not (bbox[0] < bbox[2] and bbox[1] < bbox[3]):
        parser.error("--bbox must be xmin ymin xmax ymax")
    path = download_parcels_for_bbox(bbox, refresh=args.refresh)
    print(f"✅ Saved county parcel GeoJSON snapshot: {path}")


if __name__ == "__main__":
    main()
