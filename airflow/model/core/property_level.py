"""
Helpers to run enrichment once per PropertyId and broadcast to unit rows.
ListingId = "{PropertyId}-{FloorplanId}"; property-level features are identical
across units at the same building.
"""
from __future__ import annotations

import pandas as pd

# Columns that vary by floorplan / unit — never overwrite from a property rep row.
UNIT_LEVEL_COLS = frozenset({
    "ListingId",
    "FloorplanId",
    "LegacyListingId",
    "UnitName",
    "UnitNumber",
    "ListingGranularity",
    "RoomStatus",
    "RentAmount",
    "RentMin",
    "RentMax",
    "Bedrooms",
    "Bathrooms",
    "SqFt",
    "AvailableFrom",
    "AvailableDate",
    "LengthAvailable",
    "available_bedrooms",
    "available_bathrooms",
    "rent_per_person",
    "num_people",
    "total_rent_amount",
    "extracted_rental_data",
    "ShortDescription",
    "RentType",
    "predictedrent",
    "PredictedRent",
    "fair_rent",
    "log_rent",
    "log_fair_rent",
    "actual_rent",
    "pct_mispricing",
    "mispricing",
    "mispricing_pct",
    "predicted_rent_cma",
    "nearest_neighbor_listingIds",
    "nearest_neighbor_listingids",
    "combined_bedrooms_bathrooms",
})


def ensure_property_id(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure PropertyId exists (derive from ListingId if needed)."""
    out = df.copy()
    if "PropertyId" in out.columns:
        out["PropertyId"] = out["PropertyId"].astype(str)
    elif "ListingId" in out.columns:
        out["PropertyId"] = out["ListingId"].astype(str).str.rsplit("-", n=1).str[0]
    else:
        raise ValueError("DataFrame needs PropertyId or ListingId")
    return out


def property_id_from_listing_id(listing_ids: pd.Series) -> pd.Series:
    return listing_ids.astype(str).str.rsplit("-", n=1).str[0]


def apply_per_property(df: pd.DataFrame, fn, label: str = "") -> pd.DataFrame:
    """
    Run `fn` on one representative row per PropertyId, then merge non-unit
    columns back onto every unit row of that property.
    """
    df = ensure_property_id(df)
    if df.empty:
        return df

    reps = df.drop_duplicates(subset=["PropertyId"], keep="first").copy()
    tag = f"{label}: " if label else ""
    print(f"🔑 {tag}{len(reps)} properties (of {len(df)} unit rows)")

    computed = fn(reps)
    if computed is None:
        raise ValueError(f"{label or 'apply_per_property'}: fn returned None")
    computed = ensure_property_id(computed)

    prop_cols = [c for c in computed.columns if c not in UNIT_LEVEL_COLS]
    if "PropertyId" not in prop_cols:
        prop_cols = ["PropertyId"] + prop_cols

    base = df.drop(
        columns=[c for c in prop_cols if c != "PropertyId" and c in df.columns],
        errors="ignore",
    )
    merge_frame = computed[prop_cols].drop_duplicates(subset=["PropertyId"], keep="first")
    return base.merge(merge_frame, on="PropertyId", how="left")
