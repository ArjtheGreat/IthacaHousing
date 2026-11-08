"""Property-grouped OpenAI rent-basis classification.

The model does not estimate rents, browse websites, or edit the database.
It labels the meaning of the *original* advertised amount using only source
metadata/text. Economic plausibility is not evidence of rent basis.
"""
from __future__ import annotations

import json
import os
import time

import pandas as pd

MODEL = os.getenv("RENT_BASIS_OPENAI_MODEL", "gpt-4.1-mini")
MAX_PROPERTY_FLOORPLANS = 60
SYSTEM_PROMPT = """You audit rental listing PRICING BASIS, not fair market rent.
Classify the ORIGINAL advertised amount for EACH floorplan as:
- per_person: the stated amount covers ONE person's lease/room share
- per_unit: the stated amount covers the ENTIRE rental unit
- unknown: ambiguous, conflicting, or insufficient source evidence

A property may have mixed rent conventions. Evaluate floorplans separately.
Read source descriptions, floorplan titles, explicit floorplan pricing labels,
and property-level rent labels. Property-wide labels are weak evidence when
the property offers both individual and conventional leasing.
Never infer the basis merely because a price looks cheap/expensive.
Do not use listing predictions, previously calculated per-person rents,
or derived fields such as person_rent as evidence.
An explicit quote must be a verbatim substring of source text or an exact
structured source label identifying the basis. If only indirect context is
available, use 'inferred' (or 'none'), not 'explicit'.
If ambiguous, select 'unknown'; confidence is NOT evidence.
Return one answer per supplied listingid, with no invented identifiers."""


def _clean(value, max_len=1200):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    return text[:max_len] if text and text.lower() != "nan" else None


def _source_records(group):
    prop = group.iloc[0]
    property_info = {
        "property_id": _clean(prop.get("PropertyId")),
        "address": _clean(prop.get("ListingAddress")),
        "property_rent_type": _clean(prop.get("RentType")),
        "property_description": _clean(prop.get("ShortDescription"), 2500),
        "property_leasing_features": _clean(prop.get("PropertyHighlights"), 2500),
    }
    floorplans = []
    for _, row in group.iterrows():
        floorplans.append({
            "listingid": str(row["ListingId"]),
            "rentamount": _clean(row.get("RentAmount")),
            "bedrooms": _clean(row.get("Bedrooms")),
            "bathrooms": _clean(row.get("Bathrooms")),
            "housing_type": _clean(row.get("HousingType")),
            "unit_name": _clean(row.get("UnitName")),
            "unit_number": _clean(row.get("UnitNumber")),
            "floorplan_rent_style": _clean(row.get("FloorplanRentStyle")),
            "floorplan_per_person": _clean(row.get("FloorplanPerPerson")),
            "source_description": _clean(row.get("ShortDescription"), 1000),
        })
    return {"property": property_info, "floorplans": floorplans}


def _schema():
    return {
        "name": "rent_basis_classifications",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "results": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "listingid": {"type": "string"},
                            "rent_basis": {
                                "type": "string",
                                "enum": ["per_person", "per_unit", "unknown"],
                            },
                            "confidence": {
                                "type": "string",
                                "enum": ["high", "medium", "low"],
                            },
                            "evidence_type": {
                                "type": "string",
                                "enum": ["explicit", "inferred", "none"],
                            },
                            "evidence": {"type": "string"},
                        },
                        "required": [
                            "listingid", "rent_basis", "confidence",
                            "evidence_type", "evidence",
                        ],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["results"],
            "additionalProperties": False,
        },
    }


def _verbatim_evidence(evidence, records):
    """Never accept unsupported model-generated 'quotes' as verified evidence."""
    evidence = (evidence or "").strip()
    if not evidence:
        return False
    source_text = " ".join(
        str(value)
        for value in [
            *records["property"].values(),
            *(v for row in records["floorplans"] for v in row.values()),
        ]
        if value is not None
    ).casefold()
    return evidence.casefold() in source_text


def classify_rent_bases(frame: pd.DataFrame) -> pd.DataFrame:
    """Classify every floorplan in property context; unknowns are not corrected.

    OPENAI_API_KEY is required when enabled. To bypass AI intentionally, set
    RENT_BASIS_OPENAI_ENABLED=0. Failures also stay unverified and are logged.
    """
    out = frame.copy()
    for column in (
        "rent_basis", "rent_basis_confidence", "rent_basis_evidence",
        "rent_basis_evidence_type", "rent_basis_source",
    ):
        out[column] = None

    if not os.getenv("RENT_BASIS_OPENAI_ENABLED", "1").lower() in {"1", "true", "yes"}:
        print("ℹ️ OpenAI rent-basis classification disabled by configuration")
        return out
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ OPENAI_API_KEY absent: rent basis remains unverified; no AI corrections")
        return out

    from openai import OpenAI

    client = OpenAI(timeout=35.0, max_retries=2)
    if "PropertyId" not in out:
        out["PropertyId"] = out["ListingId"].astype(str).str.rsplit("-", n=1).str[0]

    successful = 0
    for property_id, group in out.groupby("PropertyId", sort=False):
        # A very large property is split into consistent, bounded requests.
        for start in range(0, len(group), MAX_PROPERTY_FLOORPLANS):
            chunk = group.iloc[start:start + MAX_PROPERTY_FLOORPLANS]
            records = _source_records(chunk)
            allowed = set(chunk["ListingId"].astype(str))
            try:
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": json.dumps(records, ensure_ascii=False)},
                    ],
                    response_format={"type": "json_schema", "json_schema": _schema()},
                )
                result = json.loads(response.choices[0].message.content or "{}")
                classifications = result.get("results", [])
                ids = [entry.get("listingid") for entry in classifications]
                if set(ids) != allowed or len(ids) != len(allowed):
                    raise ValueError("Response IDs did not match requested floorplan IDs")

                for entry in classifications:
                    listing_id = entry["listingid"]
                    idx = chunk.index[chunk["ListingId"].astype(str) == listing_id]
                    basis = entry["rent_basis"]
                    confidence = entry["confidence"]
                    evidence_type = entry["evidence_type"]
                    evidence = entry["evidence"][:500]
                    # Downgrade invented or unverifiable "explicit" evidence.
                    # A property-level label alone can be ambiguous, so don't
                    # allow it to establish a per-person override.
                    if evidence_type == "explicit" and not _verbatim_evidence(evidence, records):
                        evidence_type = "inferred"
                    out.loc[idx, "rent_basis"] = basis
                    out.loc[idx, "rent_basis_confidence"] = confidence
                    out.loc[idx, "rent_basis_evidence"] = evidence
                    out.loc[idx, "rent_basis_evidence_type"] = evidence_type
                    out.loc[idx, "rent_basis_source"] = "openai"
                successful += len(chunk)
            except Exception as exc:
                print(f"⚠️ OpenAI rent-basis classification failed for property "
                      f"{property_id}: {type(exc).__name__}: {exc}")
            # No sleep needed: SDK retries transient errors.
    print(f"🤖 OpenAI rent-basis classified {successful}/{len(out)} floorplans")
    return out
