"""Unit-level physical configuration features for rental valuation.

Missing shared-facilities evidence stays NaN; do not assume all listings are
self-contained or label an entire mixed-floorplan property from its description.
Shared means kitchen/bath outside the separately rented unit (not roommates
sharing a kitchen within their own jointly rented apartment).
"""
from __future__ import annotations

import re
import numpy as np
import pandas as pd

# These are explicit references to communal essential facilities, not generic
# shared amenities like gyms, laundry, lounges, yards or common areas.
_SHARED = re.compile(
    r"\b(?:shared|communal|common|community)\s+"
    r"(?:kitchen(?:ette)?s?|bath(?:room)?s?|showers?|cooking facilities)\b"
    r"|\b(?:kitchen(?:ette)?s?|bath(?:room)?s?|showers?)\s+"
    r"(?:are\s+)?(?:shared|communal)\b"
    r"|\b(?:share|sharing)\s+(?:a|the|an)?\s*"
    r"(?:kitchen|bathroom|bath|shower)\b",
    flags=re.IGNORECASE,
)
_SELF_CONTAINED = re.compile(
    r"\b(?:self[- ]contained|entire|whole)\s+(?:apartment|unit|studio)\b"
    r"|\b(?:private|own|dedicated)\s+(?:apartment|unit)\b",
    flags=re.IGNORECASE,
)
_PRIVATE_KITCHEN = re.compile(
    r"\b(?:private|own|in[- ]unit|dedicated)\s+kitchen(?:ette)?\b",
    flags=re.IGNORECASE,
)
_PRIVATE_BATH = re.compile(
    r"\b(?:private|own|in[- ]unit|dedicated)\s+(?:bath(?:room)?|shower)\b",
    flags=re.IGNORECASE,
)
_ROOM_OFFER = re.compile(
    r"\b(?:furnished\s+)?rooms?\s+(?:for\s+rent|available|for\s+(?:a\s+)?single\s+person)"
    r"|\b(?:rent|priced?|leased?)\s+(?:by|per)\s+(?:the\s+)?(?:room|bedroom|bed)\b",
    flags=re.IGNORECASE,
)
_UNIT_DESCRIPTION_COLS = ("UnitDescription", "unitdescription", "FloorplanDescription", "floorplandescription")
_PROPERTY_DESCRIPTION_COLS = ("ShortDescription", "shortdescription")
_UNIT_NAME_COLS = ("UnitName", "unitname", "FloorplanName", "floorplanname")


def add_unit_configuration_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Add actual physical bedroom count and nullable shared-facilities flag.

    Bedroom count is from original unit/floorplan metadata, not the occupancy
    normalization count. Source 0 -> studio 0 even when num_people is 1.

    Shared: 1 = explicit communal essential facilities or explicitly offered
    single room; 0 = explicitly self-contained unit; NaN = insufficient evidence.
    A property-level description mentioning rooms does not classify other floor
    plans in that building (e.g., a separately offered 2BR apartment).
    """
    out = frame.copy()
    source = next((col for col in ("Bedrooms", "bedrooms") if col in out), None)
    if source is None:
        raise ValueError("Physical bedroom count is required for unit configuration")
    raw_beds = pd.to_numeric(out[source], errors="coerce")
    out["physical_bedrooms"] = raw_beds.where(raw_beds.ge(0))

    if "shared_facilities" in out.columns:
        shared = pd.to_numeric(out["shared_facilities"], errors="coerce")
        out["shared_facilities"] = shared.where(shared.isin([0, 1]))
    else:
        out["shared_facilities"] = np.nan

    for i, row in out.iterrows():
        # Preserve pre-existing, explicitly reviewed configuration flags.
        if pd.notna(out.at[i, "shared_facilities"]):
            continue

        beds = out.at[i, "physical_bedrooms"]
        unit_text = " ".join(
            str(row[col]) for col in _UNIT_DESCRIPTION_COLS + _UNIT_NAME_COLS
            if col in out and pd.notna(row[col])
        )
        property_text = " ".join(
            str(row[col]) for col in _PROPERTY_DESCRIPTION_COLS
            if col in out and pd.notna(row[col])
        )
        if unit_text:
            if _SHARED.search(unit_text):
                out.at[i, "shared_facilities"] = 1.0
                continue
            if (_SELF_CONTAINED.search(unit_text) or\n                    (_PRIVATE_KITCHEN.search(unit_text) and\n                     _PRIVATE_BATH.search(unit_text))):
                out.at[i, "shared_facilities"] = 0.0
                continue

        # A listing-level property description can describe many apartment
        # layouts, so accept it only when its explicit scope matches the unit.
        # Explicit room offers on single-room entries (1BR) are safe positive
        # evidence; multi-bedroom listings in the same building stay unknown.
        if pd.notna(beds) and beds == 1 and _ROOM_OFFER.search(property_text):
            out.at[i, "shared_facilities"] = 1.0

    print(
        "🏠 Unit configuration: "
        f"{int(out['physical_bedrooms'].eq(0).sum())} studios; "
        f"{int(out['shared_facilities'].eq(1).sum())} shared; "
        f"{int(out['shared_facilities'].eq(0).sum())} self-contained; "
        f"{int(out['shared_facilities'].isna().sum())} unknown"
    )
    return out
