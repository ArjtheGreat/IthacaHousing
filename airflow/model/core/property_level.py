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
    "unit_sqft",  # Floorplan-specific area; never broadcast across a property.
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


def _without_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Keep the first copy of any repeated column name.

    A cache query that selects the same field twice makes pandas refuse to
    align frames in ``concat`` (InvalidIndexError).
    """
    if df.columns.duplicated().any():
        return df.loc[:, ~df.columns.duplicated()].copy()
    return df


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


def apply_cached_property_enrichment(
    df: pd.DataFrame,
    existing: pd.DataFrame,
    fn,
    fields: list[str],
    label: str = "",
    required: list[str] | None = None,
) -> pd.DataFrame:
    """Reuse previously persisted property-level fields, compute only misses.

    Only rows with a usable cached value for every required field are reused.
    Fields not stored in housing_listings must continue to be recomputed.
    New Cornell source fields (such as contact details) are never overwritten.
    """
    df = _without_duplicate_columns(ensure_property_id(df))
    if df.empty:
        return df
    if existing is None or existing.empty or "listingid" not in existing.columns:
        return apply_per_property(df, fn, label=label)
    existing = _without_duplicate_columns(existing)

    available = [field for field in fields if field in existing.columns]
    required = required or available
    if not available or any(field not in existing.columns for field in required):
        return apply_per_property(df, fn, label=label)

    cached = existing.copy()
    cached["PropertyId"] = property_id_from_listing_id(cached["listingid"])
    for field in required:
        cached[field] = cached[field].replace(["", "Not Found", "nan"], pd.NA)
    cached["_completeness"] = cached[available].notna().sum(axis=1)
    cached = cached.sort_values("_completeness", ascending=False).drop_duplicates("PropertyId")
    cached = cached.loc[cached[required].notna().all(axis=1), ["PropertyId"] + available]

    # A new property's rows are processed once, and cached data is broadcast
    # to all its units without filtering out the actual rental floor plans.
    known_ids = set(cached["PropertyId"].astype(str))
    known = df.loc[df["PropertyId"].isin(known_ids)].copy()
    new = df.loc[~df["PropertyId"].isin(known_ids)].copy()
    print(f"♻️ {label}: {len(known_ids & set(df['PropertyId']))} cached properties, "
          f"{new['PropertyId'].nunique()} to compute")

    if not known.empty:
        known = known.drop(columns=available, errors="ignore").merge(
            cached, on="PropertyId", how="left", validate="many_to_one",
        )
    if not new.empty:
        new = apply_per_property(new, fn, label=label)

    return pd.concat(
        [_without_duplicate_columns(known), _without_duplicate_columns(new)],
        ignore_index=True,
        sort=False,
    )
