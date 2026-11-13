"""Explicit unit listing exclusions shared by ingestion and DB-only retraining.

IDs are Cornell property-floorplan identifiers, NOT entire PropertyIds.
Add another string here to exclude an individual unit from the next full
refresh and to delete it during a DB-only prediction rerun.
"""
from __future__ import annotations

EXCLUDED_LISTING_UNIT_IDS = frozenset({
    "237571-30678009",  # The Pinnacle, 121 Lake St: anomalous 2BR floorplan
    "237333-30766393",  # Center Ithaca, 171 E State St: R100 retail/commercial unit
})


def exclude_listing_units(frame):
    """Return a copy without explicitly excluded unit listing IDs."""
    if "ListingId" in frame.columns:
        id_col = "ListingId"
    elif "listingid" in frame.columns:
        id_col = "listingid"
    else:
        raise KeyError("Expected ListingId or listingid for unit exclusions")
    mask = frame[id_col].astype(str).str.strip().isin(EXCLUDED_LISTING_UNIT_IDS)
    if mask.any():
        print(f"🚫 Excluded {int(mask.sum())} listing-unit rows: "
              f"{sorted(frame.loc[mask, id_col].astype(str).unique())}")
    return frame.loc[~mask].copy().reset_index(drop=True)
