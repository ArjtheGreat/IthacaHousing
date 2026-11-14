"""Apply verified amenity corrections without mutating raw advertised labels."""
import os

import pandas as pd
from sqlalchemy import create_engine, text

from calculators.calculate_amenity_score import CANONICAL_AMENITY_COLUMNS


def apply_amenity_overrides(frame, overrides=None):
    out = frame.copy()
    if overrides is None:
        engine = create_engine(os.environ["DB_URI"], pool_pre_ping=True)
        try:
            with engine.connect() as conn:
                overrides = pd.read_sql(text(
                    "SELECT property_id, listing_id, feature, value "
                    "FROM public.amenity_overrides WHERE active "
                    "ORDER BY (listing_id <> ''), property_id, listing_id, feature"
                ), conn)
        finally:
            engine.dispose()
    listing_col = next((c for c in ("ListingId", "listingid") if c in out), None)
    if listing_col is None:
        raise ValueError("Amenity overrides require a stable ListingId")
    ids = out[listing_col].astype(str)
    properties = ids.str.split("-", n=1).str[0]
    count = 0
    for row in overrides.sort_values("listing_id", key=lambda s: s.ne(""), kind="stable").itertuples(index=False):
        if row.feature not in CANONICAL_AMENITY_COLUMNS:
            raise ValueError(f"Unknown canonical amenity: {row.feature}")
        mask = properties.eq(str(row.property_id))
        if row.listing_id:
            mask &= ids.eq(str(row.listing_id))
        if row.feature not in out:
            out[row.feature] = 0
        out.loc[mask, row.feature] = int(row.value)
        count += int(mask.sum())
    if {"has_in_unit_laundry", "has_shared_laundry", "has_laundry"}.issubset(out.columns):
        out["has_laundry"] = (out["has_in_unit_laundry"].eq(1) | out["has_shared_laundry"].eq(1)).astype("int8")
    print(f"Applied {count} verified listing-feature overrides")
    return out


def normalize_known_addresses(frame):
    """Keep the source unit identifier separate from the street address."""
    out = frame.copy()
    id_col = next((c for c in ("ListingId", "listingid") if c in out), None)
    if id_col is None:
        return out
    matching = out[id_col].astype(str).str.startswith("239673-")
    for col in ("ListingAddress", "listingaddress"):
        if col in out:
            out.loc[matching, col] = "201 College Avenue"
    return out
