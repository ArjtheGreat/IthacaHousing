import numpy as np
import ast

AMENITY_WEIGHTS = {
    "Electricity Included": 15,
    "Heat Included": 15,
    "Internet Available": 12,
    "Internet Included": 12,
    "Kitchen": 12,
    "Laundry Facilities": 12,
    "Air Conditioning": 10,
    "Furnished": 10,
    "Near Bus Route": 8,
    "Wheelchair Accessible": 8,
    "Off-Street Parking Included": 8,
    "Electronic Payments Accepted": 5,
    "Water Included": 5,
    "Off-Street Parking Available": 3,
    "Permitted Street Parking Available": 3
}

MAX_TOTAL_SCORE = sum(AMENITY_WEIGHTS.values())
MEDIAN_WEIGHT = np.median(list(AMENITY_WEIGHTS.values()))

def compute_amenity_score(amenities_list):
    """Compute normalized amenity score (0–100), using median for unknowns."""
    if not isinstance(amenities_list, list):
        try:
            amenities_list = ast.literal_eval(amenities_list)
        except (ValueError, SyntaxError):
            return 0

    score = sum(AMENITY_WEIGHTS.get(amenity.strip(), MEDIAN_WEIGHT) for amenity in amenities_list)
    normalized_score = (score / MAX_TOTAL_SCORE) * 100
    return round(normalized_score, 2)


def calculate_amenity_score(apartments_for_rent):
    """
    Calculates amenity score for each row
    Args:
        apartments_for_rent: dataframe with housing data
    """
    apartments_for_rent["amenities_score"] = apartments_for_rent["Amenities"].apply(
        lambda x: compute_amenity_score(x)
    )

    for amenity in AMENITY_WEIGHTS.keys():
        apartments_for_rent[amenity] = apartments_for_rent["Amenities"].apply(
            lambda x: 1 if isinstance(x, list) and amenity in x
            else 1 if isinstance(x, str) and amenity in x
            else 0
        )
        
    return apartments_for_rent

# Canonical advertised-feature indicators. These are intentionally separate from
# legacy "X Included" fields: a service being advertised does not mean it is
# included in rent. A 0 means "not advertised", not "confirmed absent".
# Each entry contains exact normalized Cornell labels to avoid partial-string
# false positives ("Furnished Packages Available" != furnished).
CANONICAL_AMENITY_ALIASES = {
    "has_ac": ("air conditioning", "central heat and air conditioning", "central ac"),
    "has_heating": ("central heat and air conditioning", "heat included", "heating"),
    "has_dishwasher": ("dishwasher",),
    "is_furnished": ("furnished", "fully furnished"),
    "has_in_unit_laundry": ("washer & dryer", "washer and dryer", "in-unit washer/dryer", "in unit laundry"),
    "has_shared_laundry": ("laundry on-site", "laundry room", "on-site laundry", "laundry facilities"),
    "has_microwave": ("microwave",),
    "has_oven": ("oven",),
    "has_refrigerator": ("refrigerator",),
    "has_stainless_appliances": ("stainless steel appliances", "stainless steel kitchen appliances"),
    "has_garbage_disposal": ("garbage disposal",),
    "has_hardwood_floors": ("hardwood floors", "wood plank flooring"),
    "has_granite_countertops": ("granite countertops",),
    "has_quartz_countertops": ("quartz countertops",),
    "has_private_bathroom": ("private bathrooms", "private bathroom"),
    "has_walk_in_closet": ("walk-in closet", "walk in closet"),
    "has_fireplace": ("fireplace",),
    "has_ceiling_fan": ("ceiling fans", "ceiling fan"),
    "has_keyless_entry": ("keyless entry", "electronic key system"),
    "has_private_entrance": ("private entrance",),
    "has_private_balcony": ("private balcony",),
    "has_porch": ("porch",),
    "has_patio": ("patio", "private patio"),
    "has_high_ceilings": ("high ceilings", "9 foot ceilings"),
    "has_fitness_center": ("fitness center", "gym", "fitness facility", "24 hour fitness center"),
    "has_pool": ("swimming pool",),
    "has_elevator": ("elevator",),
    "has_study_room": ("study room", "study lounge"),
    "has_resident_lounge": ("resident lounge", "tv lounge"),
    "has_rooftop_terrace": ("rooftop terrace",),
    "has_sauna": ("sauna",),
    "has_courtyard": ("courtyard",),
    "has_yard": ("yard",),
    "has_grill": ("grill",),
    "has_bike_storage": ("bike racks", "bike storage room"),
    "has_ev_charging": ("vehicle charging station",),
    "has_security_cameras": ("security cameras on site",),
    "has_controlled_access": ("controlled building access", "entrance secured"),
    "has_package_room": ("package room", "package lockers"),
    "has_onsite_management": ("property manager on site",),
    "has_onsite_maintenance": ("on-site maintenance",),
    "has_emergency_maintenance": ("24 hour emergency maintenance",),
    "has_storage": ("on-site storage",),
    "parking_available": ("parking available", "off-street parking available"),
    "has_private_shuttle": ("private shuttle",),
    "roommate_matching_available": ("roommate matching available",),
    "cats_allowed_advertised": ("cats",),
    "dogs_allowed_advertised": ("dogs",),
    "ada_accessible_advertised": ("ada accessible",),
    "electricity_advertised": ("electric", "electricity"),
    "water_advertised": ("water", "water & sewer"),
    "trash_advertised": ("trash",),
    "gas_advertised": ("gas",),
    "hot_water_advertised": ("hot water",),
    "internet_available": ("high speed internet", "wifi", "wi-fi", "common area wi-fi"),
    "internet_ready": ("internet ready",),
    "cable_ready": ("cable ready",),
    "snow_removal_advertised": ("snow removal",),
    "lawn_care_included": ("lawn care included",),
    "utilities_included": ("unlimited utilities included",),
    "per_person_leasing": ("per person leasing", "individual leases", "individual leases offered"),
    "academic_term_lease": ("academic year", "semester", "10-month"),
    "short_term_lease_available": ("6-month", "short or academic-term leases available"),
    "furnishing_option_available": ("furnished packages available",),
    "pets_negotiable": ("pets negotiable",),
    "no_pets_allowed": ("no pets allowed",),
}
CANONICAL_AMENITY_COLUMNS = tuple(CANONICAL_AMENITY_ALIASES) + (
    "heat_included_verified", "internet_included_verified",
    "electricity_included_verified", "water_included_verified",
    "trash_included_verified", "has_laundry",
)


def _amenity_labels(raw):
    """Handle both CSV/DB JSON arrays and the original list representation."""
    if isinstance(raw, (list, tuple, set)):
        values = raw
    elif isinstance(raw, str):
        try:
            values = ast.literal_eval(raw)
        except (ValueError, SyntaxError):
            values = []
    else:
        values = []
    if not isinstance(values, (list, tuple, set)):
        return set()
    return {" ".join(str(v).strip().casefold().split()) for v in values if isinstance(v, str)}


def extract_canonical_amenities(raw):
    labels = _amenity_labels(raw)
    flags = {
        name: int(bool(labels.intersection(aliases)))
        for name, aliases in CANONICAL_AMENITY_ALIASES.items()
    }
    flags["heat_included_verified"] = int("heat included" in labels)
    flags["internet_included_verified"] = int("internet included" in labels or "wifi included" in labels)
    flags["electricity_included_verified"] = int("electricity included" in labels or "electric included" in labels)
    flags["water_included_verified"] = int("water included" in labels or "water & sewer included" in labels)
    flags["trash_included_verified"] = int("trash included" in labels)
    flags["has_laundry"] = int(bool(flags["has_in_unit_laundry"] or flags["has_shared_laundry"]))
    return flags


def add_canonical_amenities(df, column="Amenities"):
    """Normalize each source listing; retain raw labels for future auditing."""
    out = df.copy()
    extracted = [extract_canonical_amenities(x) for x in out[column]]
    indicators = pd.DataFrame(extracted, index=out.index)
    for name in CANONICAL_AMENITY_COLUMNS:
        out[name] = indicators[name].astype("int8")
    return out
