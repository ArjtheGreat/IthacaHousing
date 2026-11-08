"""Backfill Cornell unit-level floorplan SQFT without retraining or full ETL.

From airflow/model:
    python -m ml.backfill_unit_sqft           # preview matched floorplans
    python -m ml.backfill_unit_sqft --apply   # update existing rows in Postgres

Requires DB_URI. Updates only rows with valid positive source area. Never
changes parcel assessment_sqft, listing rents, or model predictions.
"""
from __future__ import annotations

import argparse
import os

import pandas as pd
from sqlalchemy import create_engine, text

from core.fetch_housing_data import scrape_all_listings


def build_backfill_rows(scraped):
    """One valid source floorplan area per stable ListingId."""
    frame = pd.DataFrame(scraped)
    if frame.empty or "ListingId" not in frame or "unit_sqft" not in frame:
        return []
    area = pd.to_numeric(frame["unit_sqft"], errors="coerce")
    frame = frame.loc[area.notna() & (area > 0), ["ListingId"]].copy()
    frame["unit_sqft"] = area.loc[frame.index].astype(float)
    frame["listingid"] = frame["ListingId"].astype(str)
    return frame.drop_duplicates("listingid")[["listingid", "unit_sqft"]].to_dict("records")


def run_backfill(apply=False):
    db_uri = os.environ.get("DB_URI")
    if not db_uri:
        raise RuntimeError("Set DB_URI to your Supabase Postgres connection string")

    print("📥 Reading live Cornell floorplan sizes...")
    records = build_backfill_rows(scrape_all_listings())
    print(f"📐 {len(records)} floorplans have valid positive unit_sqft")

    engine = create_engine(db_uri, pool_pre_ping=True)
    with engine.connect() as conn:
        matched = conn.execute(
            text("SELECT count(*) FROM housing_listings WHERE listingid = ANY(:ids)"),
            {"ids": [r["listingid"] for r in records]},
        ).scalar_one() if records else 0
    print(f"🔗 {matched} floorplans match existing database listingid values")

    if not apply:
        print("DRY RUN: No database changes. Pass --apply to update matched areas.")
        return {"source_areas": len(records), "matched": matched, "updated": 0}

    if not records:
        print("No positive floorplan areas found, skipping update.")
        return {"source_areas": 0, "matched": 0, "updated": 0}

    statement = text("""
        UPDATE housing_listings
           SET unit_sqft = :unit_sqft
         WHERE listingid = :listingid
           AND unit_sqft IS DISTINCT FROM :unit_sqft
    """)
    with engine.begin() as conn:
        conn.execute(text(
            "ALTER TABLE housing_listings ADD COLUMN IF NOT EXISTS unit_sqft numeric"
        ))
        updated = 0
        for offset in range(0, len(records), 200):
            result = conn.execute(statement, records[offset:offset + 200])
            updated += result.rowcount

    print(f"✅ Backfilled {updated} changed floorplan areas")
    return {"source_areas": len(records), "matched": matched, "updated": updated}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write valid areas to DB")
    args = parser.parse_args()
    run_backfill(apply=args.apply)
