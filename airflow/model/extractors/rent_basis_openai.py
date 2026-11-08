"""Property-grouped OpenAI rent-basis classification.

The model does not estimate rents, browse websites, or edit the database.
It labels the meaning of the *original* advertised amount using only source
metadata/text. Economic plausibility is not evidence of rent basis.
"""
from __future__ import annotations

import hashlib
import json
import os

import pandas as pd
from sqlalchemy import create_engine, text

MODEL = os.getenv("RENT_BASIS_OPENAI_MODEL", "gpt-4.1-mini")
MAX_PROPERTY_FLOORPLANS = 60
CLASSIFIER_VERSION = "rent-basis-v3-evidence-fields-2026-11"
SYSTEM_PROMPT = """Classify the basis of the ORIGINAL advertised rental price.
For each floorplan, return per_person, per_unit, or unknown.

Crucial: The input deliberately excludes Cornell's property-level RentType.
That field is sometimes INCORRECT. Do not assume that a low rent is per person
or a high rent is per unit. Do not use market estimates or fair rent predictions.

Evidence hierarchy:
1. Explicit price-basis language in the floorplan's unit_name,
   source_description, floorplan_rent_style, or floorplan_per_person.
2. Explicit language in property_description which clearly applies to this
   type of floorplan (e.g. 'Two and three bedroom unit pricing is listed by bed').
3. Property_leasing_features provide CONTEXT ONLY, never verification:
   'individual leases offered' or 'per person leasing available' alone does
   not prove a particular floorplan's advertised price is per person.

When explicit evidence supports one classification, output confidence high,
evidence_type explicit, evidence_source EXACTLY one of:
unit_name, source_description, floorplan_rent_style, floorplan_per_person,
property_description. evidence must be an EXACT CONTIGUOUS SUBSTRING from
that source field (no summary, quote marks added, or 'source says' prefix).
Examples of strong language: 'by the bed rent price', 'rent per bedroom',
'pricing is listed by bed', 'rent is $1,000 per room', 'entire unit rent'.
A unit named '1 in 3 Bed Unit' is suggestive, NOT explicit.

If context implies a basis but no exact source statement supports it,
return evidence_type inferred, confidence medium or low, and source field
'none'. If source details are insufficient or contradictory, return unknown.
NEVER claim high confidence based just on missing contradictory evidence.
Never invent quotes. Return one result for every provided listingid."""



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


def _fingerprint(records):
    """Invalidate classification on any changed source evidence, prompt, or model."""
    payload = {
        "version": CLASSIFIER_VERSION,
        "model": MODEL,
        "prompt": SYSTEM_PROMPT,
        "records": records,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _load_cached_results():
    """Fetch prior decisions BEFORE the full-refresh TRUNCATE TABLE.

    Older schemas without these fields safely behave as an empty cache.
    """
    uri = os.getenv("DB_URI")
    if not uri:
        print("ℹ️ No DB_URI; rent basis cache unavailable")
        return {}
    engine = create_engine(uri, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            required = {
                "listingid", "rent_basis", "rent_basis_confidence",
                "rent_basis_evidence", "rent_basis_evidence_type",
                "rent_basis_source", "rent_basis_evidence_field",
                "rent_basis_fingerprint",
            }
            present = {
                row[0] for row in conn.execute(text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema = 'public' AND table_name = 'housing_listings'"
                ))
            }
            if not required.issubset(present):
                print("ℹ️ No persisted rent-basis cache columns yet; first run audits listings")
                return {}
            rows = conn.execute(text(
                "SELECT listingid, rent_basis, rent_basis_confidence, "
                "rent_basis_evidence, rent_basis_evidence_type, "
                "rent_basis_source, rent_basis_evidence_field, rent_basis_fingerprint "
                "FROM housing_listings "
                "WHERE rent_basis_confidence IS NOT NULL "
                "AND rent_basis_fingerprint IS NOT NULL"
            )).mappings()
            return {str(row["listingid"]): dict(row) for row in rows}
    except Exception as exc:
        print(f"⚠️ Could not load prior rent-basis classifications: {exc}")
        return {}
    finally:
        engine.dispose()


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
                            "evidence_source": {"type": "string", "enum": [
                                "unit_name", "source_description", "floorplan_rent_style",
                                "floorplan_per_person", "property_description", "none"
                            ]},
                        },
                        "required": [
                            "listingid", "rent_basis", "confidence",
                            "evidence_type", "evidence", "evidence_source",
                        ],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["results"],
            "additionalProperties": False,
        },
    }


# Only these original source fields can verify an advertised rent basis.
FLOORPLAN_EVIDENCE_FIELDS = frozenset({
    "unit_name", "source_description",
    "floorplan_rent_style", "floorplan_per_person",
})
PROPERTY_EVIDENCE_FIELDS = frozenset({"property_description"})


def _explicit_basis(quote, basis):
    """Conservative vocabulary of actual price-basis statements."""
    import re

    phrase = " ".join((quote or "").casefold().split())
    # A marketing claim about optional individual leasing is not a statement
    # that THIS advertised dollar amount represents a per-person price.
    if ("leasing" in phrase or "lease" in phrase) and any(
        marker in phrase for marker in (
            "available", "offered", "optional", "option", "may choose",
        )
    ) and not any(marker in phrase for marker in (
        "rent is", "rent per", "price is", "pricing is", "price per",
        "pricing per", "listed by bed", "by the bed rent",
    )):
        return False
    if basis == "per_person":
        # 'Rent by the bed' is price-specific; 'individual leases offered'
        # is not. Require a reference to rent/pricing for isolated 'by the bed'.
        return bool(re.search(
            r"(?:per\s+(?:person|bedroom|bed|room)|"
            r"by\s+the\s+bed\s+(?:rent|price|pricing)|"
            r"(?:rent|price|pricing)\s+(?:\w+\s+){0,5}by\s+(?:the\s+)?bed|"
            r"price\s+is\s+for\s+(?:a\s+)?room\s+only|"
            r"rent\s+is\s+[^.]{0,40}per\s+room)",
            phrase,
        ))
    if basis == "per_unit":
        return bool(re.search(
            r"(?:per\s+unit|entire\s+(?:apartment|unit|home)\s+rent|"
            r"(?:rent|price|pricing)\s+(?:for\s+)?(?:the\s+)?"
            r"(?:whole|entire)\s+(?:unit|apartment|home)|"
            r"total\s+(?:apartment|unit)\s+rent)",
            phrase,
        ))
    return False


def validate_explicit_evidence(entry, records):
    """Recompute verification from actual fields, not model confidence."""
    source = entry.get("evidence_source")
    basis = entry.get("rent_basis")
    quote = (entry.get("evidence") or "").strip()
    if source not in FLOORPLAN_EVIDENCE_FIELDS | PROPERTY_EVIDENCE_FIELDS:
        return False
    if len(quote) < 8 or not _explicit_basis(quote, basis):
        return False

    floorplan = next(
        (row for row in records["floorplans"]
         if row["listingid"] == entry.get("listingid")),
        None,
    )
    if floorplan is None:
        return False
    value = (floorplan if source in FLOORPLAN_EVIDENCE_FIELDS
             else records["property"]).get(source)
    if not isinstance(value, str) or quote.casefold() not in value.casefold():
        return False

    # Property-wide qualifications must not be applied to excluded floorplans
    # e.g. a 1BR in a building describing "2 and 3 bedroom pricing by bed".
    if source == "property_description":
        import re
        context = " ".join(value.casefold().split())
        bed = pd.to_numeric(floorplan.get("bedrooms"), errors="coerce")
        qualified = re.search(
            r"(?:two\s+and\s+three|2\s+and\s+3|2\s*-\s*3)\s*"
            r"bedroom[^.]{0,100}(?:by\s+(?:the\s+)?bed|per\s+(?:person|bed))",
            context,
        )
        if qualified and pd.notna(bed) and int(bed) not in (2, 3):
            return False
    return True



def classify_rent_bases(frame: pd.DataFrame) -> pd.DataFrame:
    """Classify every floorplan in property context; unknowns are not corrected.

    OPENAI_API_KEY is required when enabled. To bypass AI intentionally, set
    RENT_BASIS_OPENAI_ENABLED=0. Failures also stay unverified and are logged.
    """
    out = frame.copy()
    for column in (
        "rent_basis", "rent_basis_confidence", "rent_basis_evidence",
        "rent_basis_evidence_type", "rent_basis_source",
        "rent_basis_evidence_field", "rent_basis_fingerprint",
    ):
        out[column] = None

    if not os.getenv("RENT_BASIS_OPENAI_ENABLED", "1").lower() in {"1", "true", "yes"}:
        print("ℹ️ OpenAI rent-basis classification disabled by configuration")
        return out
    from openai import OpenAI

    prior = _load_cached_results()
    client = None
    if "PropertyId" not in out:
        out["PropertyId"] = out["ListingId"].astype(str).str.rsplit("-", n=1).str[0]

    successful = 0
    reused = 0
    failed = 0
    for property_id, group in out.groupby("PropertyId", sort=False):
        # A very large property is split into consistent, bounded requests.
        for start in range(0, len(group), MAX_PROPERTY_FLOORPLANS):
            chunk = group.iloc[start:start + MAX_PROPERTY_FLOORPLANS]
            records = _source_records(chunk)
            fingerprint = _fingerprint(records)
            # A classification is reusable only if the *full property context*
            # is unchanged. Even "unknown" is cached to avoid repeated spend.
            cached = {
                lid: prior[lid] for lid in chunk["ListingId"].astype(str)
                if lid in prior
                and prior[lid].get("rent_basis_fingerprint") == fingerprint
                and prior[lid].get("rent_basis") in {"per_person", "per_unit", "unknown"}
                and prior[lid].get("rent_basis_confidence") in {"high", "medium", "low"}
                and prior[lid].get("rent_basis_evidence_type") in {"explicit", "inferred", "none"}
            }
            if len(cached) == len(chunk):
                for lid, previous in cached.items():
                    idx = chunk.index[chunk["ListingId"].astype(str) == lid]
                    for name in (
                        "rent_basis", "rent_basis_confidence", "rent_basis_evidence",
                        "rent_basis_evidence_type", "rent_basis_source",
                        "rent_basis_evidence_field", "rent_basis_fingerprint",
                    ):
                        out.loc[idx, name] = previous.get(name)
                reused += len(chunk)
                continue

            if not os.getenv("OPENAI_API_KEY"):
                failed += len(chunk)
                continue
            if client is None:
                client = OpenAI(timeout=35.0, max_retries=2)
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
                    evidence_source = entry["evidence_source"]
                    # Downgrade invented or unverifiable "explicit" evidence.
                    # A property-level label alone can be ambiguous, so don't
                    # allow it to establish a per-person override.
                    if evidence_type == "explicit" and not validate_explicit_evidence(entry, records):
                        evidence_type = "inferred"
                        confidence = "medium"
                    # High confidence without source evidence is not verified.
                    if evidence_type != "explicit" and confidence == "high":
                        confidence = "medium"
                    out.loc[idx, "rent_basis"] = basis
                    out.loc[idx, "rent_basis_confidence"] = confidence
                    out.loc[idx, "rent_basis_evidence"] = evidence
                    out.loc[idx, "rent_basis_evidence_type"] = evidence_type
                    out.loc[idx, "rent_basis_evidence_field"] = evidence_source
                    out.loc[idx, "rent_basis_source"] = "openai"
                    out.loc[idx, "rent_basis_fingerprint"] = fingerprint
                successful += len(chunk)
            except Exception as exc:
                failed += len(chunk)
                print(f"⚠️ OpenAI rent-basis classification failed for property "
                      f"{property_id}: {type(exc).__name__}: {exc}")
            # No sleep needed: SDK retries transient errors.
    if failed and not os.getenv("OPENAI_API_KEY"):
        print("⚠️ No OPENAI_API_KEY; unresolved rent basis remains source-derived")
    print(f"🤖 Rent-basis cache: {reused} reused, {successful} classified, "
          f"{failed} failed out of {len(out)} floorplans")
    return out
