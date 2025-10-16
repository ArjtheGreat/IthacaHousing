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

    return apartments_for_rent