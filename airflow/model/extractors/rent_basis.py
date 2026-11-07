"""Auditable floor-plan rent basis classification for Cornell listings.

The source property-wide rent_style is not always correct at floor-plan level.
The source person_rent / unit_rent fields are *derived*, not an independent
indicator of whether min_rent is a total-unit or per-person asking rent.

An uncertain rent basis is deliberately unresolved rather than silently
becoming a wildly incorrect per-person training label.
"""

import re

import numpy as np
import pandas as pd


def _number(value):
    parsed = pd.to_numeric(value, errors="coerce")
    return float(parsed) if pd.notna(parsed) and np.isfinite(parsed) else None


def _explicit_floorplan_basis(row):
    # Optional future floor-plan flags; current Cornell listingData lacks them.
    style = str(row.get("FloorplanRentStyle") or "").strip().casefold()
    if style in {"person", "per_person", "per person", "bed", "per_bed", "per bed", "room", "per_room"}:
        return "per_person"
    if style in {"unit", "per_unit", "per unit", "apartment", "entire"}:
        return "per_unit"
    flag = row.get("FloorplanPerPerson")
    if isinstance(flag, (bool, np.bool_)):
        return "per_person" if flag else "per_unit"
    if str(flag).strip().lower() in {"true", "false", "1", "0"}:
        return "per_person" if str(flag).strip().lower() in {"true", "1"} else "per_unit"
    return None


def _room_name(name):
    name = str(name or "").strip().casefold()
    return bool(re.search(r"\b(?:room\s*#?\s*[a-z]?\d+|bedroom\s*[a-z]?\d+|private\s+room|individual\s+room)\b", name))


def classify_rent_basis(frame):
    """Return an aligned dataframe with rent_basis, reason, confidence.

    A peer-based override requires >=2 comparable *whole-unit-like* floor plans
    in the same property. The raw asking rent itself is not a direct basis flag.
    Otherwise highly suspicious low per-bedroom rents are withheld for review.
    """
    result = frame.copy()
    for col in ("PropertyId", "UnitName", "RentAmount", "Bedrooms", "RentType"):
        if col not in result.columns:
            result[col] = np.nan

    result["_raw_rent"] = pd.to_numeric(result["RentAmount"], errors="coerce")
    result["_beds"] = pd.to_numeric(result["Bedrooms"], errors="coerce")
    result["_occupancy"] = result["_beds"].where(result["_beds"] > 0, 1)

    # Compare with plausible whole-unit siblings, not with a marketwide threshold
    # or a model prediction. This is supporting evidence, not source metadata.
    peer = (
        (result["_beds"] >= 2) & (result["_beds"] <= 12)
        & (result["_raw_rent"] >= 1200)
        & (result["_raw_rent"] / result["_beds"] >= 450)
        & (result["_raw_rent"] / result["_beds"] <= 3500)
        & ~result["UnitName"].fillna("").map(_room_name)
        & ~result.apply(lambda row: _explicit_floorplan_basis(row) == "per_person", axis=1)
    )
    peer_rates = (
        result.loc[peer].assign(_peer_rate=lambda x: x["_raw_rent"] / x["_beds"])
        .groupby("PropertyId", dropna=True)["_peer_rate"].agg(["median", "count"])
    )

    bases, reasons, confidences = [], [], []
    for _, row in result.iterrows():
        rent = _number(row["_raw_rent"])
        bedrooms = _number(row["_beds"])
        occupancy = _number(row["_occupancy"])
        prop = row.get("PropertyId")
        siblings = peer_rates.loc[prop] if pd.notna(prop) and prop in peer_rates.index else None

        def classify(basis, reason, confidence):
            bases.append(basis)
            reasons.append(reason)
            confidences.append(confidence)

        if rent is None or rent <= 0:
            classify("unknown", "missing_or_invalid_asking_rent", "low")
            continue

        explicit = _explicit_floorplan_basis(row)
        if explicit:
            classify(explicit, "explicit_floorplan_pricing_field", "high")
            continue
        if _room_name(row.get("UnitName")):
            classify("per_room", "explicit_room_unit_name", "high")
            continue

        # Strong within-building evidence: same price scale as reliable 2-12 BR
        # whole-unit floor plans, but dividing by 17-19 bedrooms gives $60.
        if bedrooms is not None and bedrooms >= 4 and siblings is not None and siblings["count"] >= 2:
            median = float(siblings["median"])
            if 0.70 <= rent / median <= 1.30 and rent / occupancy < 0.50 * median:
                classify("per_person", "matches_sibling_whole_unit_per_bedroom_prices", "high")
                continue

        # Property-wide explicit person pricing is meaningful, but is not a
        # guarantee when one property includes both entire-unit and room rents.
        source_type = str(row.get("RentType") or "").casefold()
        if "person" in source_type:
            classify("per_person", "source_property_per_person_flag", "medium")
            continue

        if bedrooms is None or bedrooms < 0:
            classify("unknown", "missing_bedroom_count_for_unit_pricing", "low")
        elif bedrooms >= 2 and rent / occupancy < 400:
            classify("unknown", "implausibly_low_per_bedroom_if_whole_unit", "low")
        else:
            classify("per_unit", "source_property_unit_default_no_conflicting_evidence", "medium")

    return pd.DataFrame({
        "rent_basis": bases,
        "rent_basis_reason": reasons,
        "rent_basis_confidence": confidences,
    }, index=frame.index)
