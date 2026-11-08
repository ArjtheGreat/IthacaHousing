"""
Listing assistant for the /listings page.

The user types what they want ("2 bed under $1,200 within a 15 minute walk of the Arts Quad").
Claude reads every listing on the map, picks the Personal Preferences filters that match the
request, and recommends 3-5 listings with a short reason for each. The frontend applies the
filters and highlights the picks.

Needs ANTHROPIC_API_KEY in the environment (backend/.env works, db.py loads it).
"""

import json
import logging
import math
import os
import time
from typing import List, Literal, Optional

import anthropic
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from db import get_db

router = APIRouter()

MODEL = "claude-opus-5-5"

# Must match the Personal Preferences dropdowns in MapView.vue / utils/budget.ts
BED_OPTIONS = [1, 2, 3, 4, 5]  # 5 means 5+
BATH_OPTIONS = [1, 1.5, 2, 2.5, 3]  # 3 means 3+
BUDGET_OPTIONS = [800, 1000, 1200, 1500, 2000]
COMMUTE_TIMES = [15, 20, 25, 30]
DESTINATIONS = {
    "agriculturequad": "Ag Quad",
    "artsquad": "Arts Quad",
    "engineeringquad": "Engineering Quad",
}
MODES = ["walk", "bike", "drive"]

MAX_RECOMMENDATIONS = 5
LISTINGS_TTL_SECONDS = 600  # listings change once a day at most; keeps the prompt cache warm

_client: Optional[anthropic.Anthropic] = None
_listings_cache = {"at": 0.0, "rows": None, "table": None}


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(timeout=90.0)
    return _client


# ---------- Request / response ----------

class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class CurrentFilters(BaseModel):
    beds: Optional[float] = None
    baths: Optional[float] = None
    budget: Optional[int] = None
    destination: Optional[str] = None
    mode: Optional[str] = None
    max_time: Optional[int] = None


class AssistantRequest(BaseModel):
    messages: List[ChatTurn] = Field(min_length=1, max_length=20)
    current_filters: Optional[CurrentFilters] = None


# ---------- Listing data ----------

def _num(value):
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return int(f) if f.is_integer() else round(f, 1)


def _short(value, limit):
    if not value:
        return None
    s = " ".join(str(value).split())
    return s if len(s) <= limit else s[: limit - 1] + "…"


def _plain_list(value):
    """'["Oven", "Laundry"]' -> 'Oven, Laundry'"""
    if not value:
        return None
    try:
        items = json.loads(value)
        if isinstance(items, list):
            return ", ".join(str(i) for i in items)
    except (TypeError, ValueError):
        pass
    return str(value)


TABLE_COLUMNS = ["id", "address", "rent_pp", "fair_rent_pp", "people", "beds", "baths", "available",
                 "neighborhood", "walk", "bike", "drive", "pets", "amenities", "desc"]


def format_table(listings) -> str:
    """Pipe-delimited table, one listing per line, sorted by address. Commute columns are Ag/Arts/Eng minutes."""
    def cell(v):
        return "" if v is None else str(v).replace("|", "/")

    lines = [" | ".join(TABLE_COLUMNS)]
    prev = {}
    for l in listings:
        row = []
        for col in TABLE_COLUMNS:
            if col in ("address", "neighborhood", "pets", "amenities", "desc") and l.get(col) and l.get(col) == prev.get(col):
                row.append("^")  # same as the row above (units in one building repeat these)
            elif col in MODES:
                times = [l.get(f"{col}_{d}") for d in DESTINATIONS]
                row.append("/".join("" if t is None else str(round(t)) for t in times))
            else:
                row.append(cell(l.get(col)))
        lines.append(" | ".join(row))
        prev = l
    return "\n".join(lines)


def load_listings(db: Session):
    """Every listing the map can show (same WHERE as /listings-minimal), plus the text Claude needs to judge fit."""
    now = time.time()
    if _listings_cache["rows"] is not None and now - _listings_cache["at"] < LISTINGS_TTL_SECONDS:
        return _listings_cache["rows"], _listings_cache["table"]

    rows = db.execute(text("""
        SELECT listingid, listingaddress, rent_per_person, total_rent_amount, num_people,
               available_bedrooms, available_bathrooms, housingtype, pets, amenities,
               shortdescription, dateavailable, neighborhood, predictedrent,
               walk_time_agriculturequad, walk_time_artsquad, walk_time_engineeringquad,
               bike_time_agriculturequad, bike_time_artsquad, bike_time_engineeringquad,
               drive_time_agriculturequad, drive_time_artsquad, drive_time_engineeringquad
        FROM housing_listings
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND rent_per_person IS NOT NULL
        ORDER BY listingaddress, listingid
    """)).mappings().all()

    listings = []
    for r in rows:
        listing = {
            "id": str(r["listingid"]),
            "address": r["listingaddress"],
            "rent_pp": _num(r["rent_per_person"]),
            "total_rent": _num(r["total_rent_amount"]),
            "people": _num(r["num_people"]),
            "beds": _num(r["available_bedrooms"]),
            "baths": _num(r["available_bathrooms"]),
            "type": r["housingtype"],
            "pets": _short(r["pets"], 30),
            "amenities": _short(_plain_list(r["amenities"]), 120),
            "desc": _short(r["shortdescription"], 110),
            "available": r["dateavailable"].date().isoformat() if r["dateavailable"] else None,
            "neighborhood": r["neighborhood"],
            "fair_rent_pp": round(_num(r["predictedrent"])) if _num(r["predictedrent"]) is not None else None,
        }
        for mode in MODES:
            for dest in DESTINATIONS:
                listing[f"{mode}_{dest}"] = _num(r[f"{mode}_time_{dest}"])
        listings.append(listing)

    table = format_table(listings)
    by_id = {l["id"]: l for l in listings}
    _listings_cache.update(at=now, rows=by_id, table=table)
    return by_id, table


# ---------- Filters (mirror MapView.vue so the picks stay visible on the map) ----------

def passes_filters(listing, f) -> bool:
    beds = f.get("beds")
    if beds:
        if listing["beds"] is None:
            return False
        if beds >= BED_OPTIONS[-1] and listing["beds"] < beds:
            return False
        if beds < BED_OPTIONS[-1] and listing["beds"] != beds:
            return False

    baths = f.get("baths")
    if baths:
        if listing["baths"] is None:
            return False
        if baths >= BATH_OPTIONS[-1] and listing["baths"] < baths:
            return False
        if baths < BATH_OPTIONS[-1] and listing["baths"] != baths:
            return False

    budget = f.get("budget")
    if budget:
        rent = listing["rent_pp"]
        if not rent or rent <= 0 or rent > budget:
            return False

    commute = f.get("commute")
    if commute:
        t = listing.get(f"{commute['mode']}_{commute['destination']}")
        if t is None or t >= commute["max_time"]:
            return False
    return True


def clean_filters(raw) -> dict:
    """Drop any value the dropdowns can't show, so the UI and the server agree on what's applied."""
    f = {}
    if raw.get("beds") in BED_OPTIONS:
        f["beds"] = raw["beds"]
    if raw.get("baths") in BATH_OPTIONS:
        f["baths"] = raw["baths"]
    if raw.get("budget") in BUDGET_OPTIONS:
        f["budget"] = raw["budget"]
    c = raw.get("commute")
    if c and c.get("destination") in DESTINATIONS and c.get("mode") in MODES and c.get("max_time") in COMMUTE_TIMES:
        f["commute"] = {"destination": c["destination"], "mode": c["mode"], "max_time": c["max_time"]}
    return f


# ---------- Prompt ----------

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "reply": {
            "type": "string",
            "description": "2-4 sentences to the user: what you understood, which filters you set, and anything you couldn't match.",
        },
        "filters": {
            "type": "object",
            "properties": {
                "beds": {"anyOf": [{"type": "integer", "enum": BED_OPTIONS}, {"type": "null"}]},
                "baths": {"anyOf": [{"type": "number", "enum": BATH_OPTIONS}, {"type": "null"}]},
                "budget": {"anyOf": [{"type": "integer", "enum": BUDGET_OPTIONS}, {"type": "null"}]},
                "commute": {
                    "anyOf": [
                        {
                            "type": "object",
                            "properties": {
                                "destination": {"type": "string", "enum": list(DESTINATIONS)},
                                "mode": {"type": "string", "enum": MODES},
                                "max_time": {"type": "integer", "enum": COMMUTE_TIMES},
                            },
                            "required": ["destination", "mode", "max_time"],
                            "additionalProperties": False,
                        },
                        {"type": "null"},
                    ]
                },
            },
            "required": ["beds", "baths", "budget", "commute"],
            "additionalProperties": False,
        },
        "recommendations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["id", "reason"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["reply", "filters", "recommendations"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = f"""You are the housing assistant on Ithaca Insights, a map of rental listings near Cornell University in Ithaca, NY. Students describe what they want; you set the map's filters and recommend specific listings.

## Filters you control
The map has these filters. Return the full filter state the user should see (null = "Any"); it replaces whatever is set now.
- beds: available bedrooms, one of {BED_OPTIONS}. 5 means 5 or more; the others are exact matches.
- baths: available bathrooms, one of {BATH_OPTIONS}. 3 means 3 or more; the others are exact matches.
- budget: max rent PER PERSON per month, one of {BUDGET_OPTIONS}. If the user's cap falls between options, use the smallest option at or above it, and keep your recommendations under their actual number.
- commute: destination ({", ".join(f"{k} = {v}" for k, v in DESTINATIONS.items())}), mode ({", ".join(MODES)}), max_time in minutes ({COMMUTE_TIMES}). All three or null. Commute times are strictly less than max_time.

Only set a filter the user asked for (directly or clearly implied). "Near campus" or "walkable" with no destination: pick artsquad + walk + a sensible max_time. Keep filters from earlier turns unless the user changes or drops them. If a filter combination would leave nothing, loosen the least important one and say so.

## Recommendations
Recommend 3-5 listings (by their exact "id") that pass every filter you set and best fit the whole request, including things filters can't express (pets, amenities, laundry, parking, furnished, move-in date, value). Prefer listings that are a good deal: "fair_rent_pp" is our model's fair rent per person; rent_pp below it is a good deal. Spread picks across different addresses when you can. Each "reason" is one or two short sentences naming concrete facts from the listing (rent, beds, commute minutes, amenities) — never invent details that aren't in the data. If nothing fits, return an empty list and explain in "reply".

## Listing data
A pipe-delimited table, one listing per line: id, address, rent_pp (rent per person, $/month), fair_rent_pp, people, beds, baths, available (move-in date), neighborhood, then commute minutes by walk, bike and drive, each written Ag/Arts/Eng (e.g. walk "12/8/15" = 12 min to Ag Quad, 8 to Arts Quad, 15 to Eng Quad), then pets, amenities, desc (both truncated). Rows are sorted by address; "^" means "same as the row above" (units in one building share these). Empty cells are unknown.
"""


def build_messages(req: AssistantRequest):
    msgs = [{"role": t.role, "content": t.content} for t in req.messages]
    if msgs[0]["role"] != "user" or msgs[-1]["role"] != "user":
        raise HTTPException(status_code=400, detail="Conversation must start and end with a user message")
    if req.current_filters:
        cf = req.current_filters.model_dump(exclude_none=True)
        if cf:
            msgs[-1] = {
                "role": "user",
                "content": f"{msgs[-1]['content']}\n\n(Filters currently set on the map: {json.dumps(cf)})",
            }
    return msgs


@router.post("/assistant/recommend")
def recommend(req: AssistantRequest, db: Session = Depends(get_db)):
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=503, detail="The assistant isn't configured yet (no ANTHROPIC_API_KEY).")
    by_id, table = load_listings(db)

    try:
        response = get_client().beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}},
            system=[
                {"type": "text", "text": SYSTEM_PROMPT},
                # Listings are the big, stable part of the prompt: cache them
                {"type": "text", "text": f"<listings>\n{table}\n</listings>", "cache_control": {"type": "ephemeral"}},
            ],
            messages=build_messages(req),
        )
    except anthropic.AuthenticationError:
        logging.exception("Assistant: bad or missing ANTHROPIC_API_KEY")
        raise HTTPException(status_code=503, detail="The assistant isn't configured yet.")
    except anthropic.RateLimitError:
        raise HTTPException(status_code=429, detail="The assistant is busy. Try again in a moment.")
    except anthropic.APIStatusError as e:
        logging.exception("Assistant: Claude API error")
        raise HTTPException(status_code=502, detail=f"Claude API error ({e.status_code}).")
    except anthropic.APIConnectionError:
        raise HTTPException(status_code=502, detail="Couldn't reach Claude. Try again.")
    except anthropic.AnthropicError:
        # e.g. no ANTHROPIC_API_KEY set, raised before any request goes out
        logging.exception("Assistant: client not configured")
        raise HTTPException(status_code=503, detail="The assistant isn't configured yet.")

    if response.stop_reason == "refusal":
        return {"reply": "Sorry, I can't help with that request.", "filters": None, "recommendations": []}
    if response.stop_reason == "max_tokens":
        raise HTTPException(status_code=502, detail="The assistant's answer was cut off. Try a shorter request.")

    text_block = next((b.text for b in response.content if b.type == "text"), None)
    try:
        data = json.loads(text_block or "")
    except json.JSONDecodeError:
        logging.error("Assistant: unparseable output: %r", text_block)
        raise HTTPException(status_code=502, detail="The assistant returned an unreadable answer.")

    filters = clean_filters(data.get("filters") or {})

    # Keep only real listings that are actually visible under the chosen filters
    seen, recommendations = set(), []
    for rec in data.get("recommendations") or []:
        listing = by_id.get(str(rec.get("id")))
        if not listing or listing["id"] in seen or not passes_filters(listing, filters):
            continue
        seen.add(listing["id"])
        recommendations.append({
            "listingid": listing["id"],
            "address": listing["address"],
            "rent_per_person": listing["rent_pp"],
            "beds": listing["beds"],
            "baths": listing["baths"],
            "reason": rec.get("reason", ""),
        })
        if len(recommendations) == MAX_RECOMMENDATIONS:
            break

    logging.info(
        "Assistant usage: in=%s cache_read=%s cache_write=%s out=%s",
        response.usage.input_tokens,
        response.usage.cache_read_input_tokens,
        response.usage.cache_creation_input_tokens,
        response.usage.output_tokens,
    )

    return {
        "reply": data.get("reply", ""),
        "filters": {
            "beds": filters.get("beds"),
            "baths": filters.get("baths"),
            "budget": filters.get("budget"),
            "commute": filters.get("commute"),
        },
        "recommendations": recommendations,
    }
