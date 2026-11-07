"""Regression tests for Cornell floorplan matching and per-person rents."""
import sys
from pathlib import Path
import unittest

import pandas as pd

MODEL_DIR = Path(__file__).resolve().parents[1] / "model"
sys.path.insert(0, str(MODEL_DIR))

from core.fetch_housing_data import fill_layout_from_matching_floorplans, rows_from_data
from extractors.extract_rental_data import deterministic_extract, extract_rental_data


class RentalNormalizationTests(unittest.TestCase):
    def test_same_named_unit_recovers_missing_beds_and_baths(self):
        rows = [
            {"PropertyId": "43979", "ListingId": "43979-a",
             "UnitName": "Ground Floor Garden Apt", "Bedrooms": 3.0,
             "Bathrooms": 1.0, "RentAmount": 2850.0},
            {"PropertyId": "43979", "ListingId": "43979-b",
             "UnitName": "Ground Floor Garden Apt", "Bedrooms": None,
             "Bathrooms": None, "RentAmount": 2750.0},
            {"PropertyId": "43979", "ListingId": "43979-c",
             "UnitName": "Room 203", "Bedrooms": None,
             "Bathrooms": None, "RentAmount": 950.0},
        ]
        result = fill_layout_from_matching_floorplans(rows)
        self.assertEqual(result[1]["Bedrooms"], 3.0)
        self.assertEqual(result[1]["Bathrooms"], 1.0)
        self.assertIsNone(result[2]["Bedrooms"])
        normalized = deterministic_extract({**result[1], "RentType": "Price Per Unit"})
        self.assertAlmostEqual(normalized["rent_per_person"], 2750 / 3)
        self.assertEqual(normalized["total_rent_amount"], 2750)

    def test_conflicting_sibling_layouts_are_not_guessed(self):
        rows = [
            {"PropertyId": "1", "UnitName": "Suite A", "Bedrooms": 2},
            {"PropertyId": "1", "UnitName": "Suite A", "Bedrooms": 3},
            {"PropertyId": "1", "UnitName": "Suite A", "Bedrooms": None},
            {"PropertyId": "2", "UnitName": "Suite A", "Bedrooms": None},
        ]
        result = fill_layout_from_matching_floorplans(rows)
        self.assertIsNone(result[2]["Bedrooms"])
        self.assertIsNone(result[3]["Bedrooms"])

    def test_unknown_bedrooms_do_not_inflate_per_person_rent(self):
        result = deterministic_extract({
            "Bedrooms": None, "Bathrooms": None,
            "RentAmount": 2750, "RentType": "Price Per Unit",
        })
        self.assertTrue(pd.isna(result["rent_per_person"]))
        self.assertTrue(pd.isna(result["num_people"]))
        self.assertEqual(result["total_rent_amount"], 2750)

    def test_per_person_rate_does_not_require_bedroom_count(self):
        result = deterministic_extract({
            "Bedrooms": None, "Bathrooms": None,
            "RentAmount": 950, "RentType": "Price per Person",
        })
        self.assertEqual(result["rent_per_person"], 950)

    def test_current_rent_replaces_stale_cached_values(self):
        raw = pd.DataFrame([{
            "ListingId": "46681-30722350",
            "Bedrooms": 1, "Bathrooms": 1,
            "RentAmount": 2355, "RentType": "Price Per Unit",
        }])
        result = extract_rental_data(raw)
        self.assertEqual(result.loc[0, "rent_per_person"], 2355)
        self.assertEqual(result.loc[0, "total_rent_amount"], 2355)

    def test_full_floorplan_scrape_reconciles_named_siblings(self):
        data = {"43979": {
            "id": 43979, "title": "301 Dryden Road",
            "address": "301 Dryden Rd Ithaca, NY 14850",
            "floorplans": [
                {"id": 10, "title": "Ground Floor Garden Apt",
                 "bed": 3, "bath": 1, "min_rent": "2850"},
                {"id": 11, "title": "Ground Floor Garden Apt",
                 "bed": None, "bath": None, "min_rent": "2750"},
            ],
        }}
        rows = rows_from_data(data)
        self.assertEqual(rows[1]["Bedrooms"], 3)
        self.assertEqual(rows[1]["Bathrooms"], 1)
        self.assertAlmostEqual(
            deterministic_extract(rows[1])["rent_per_person"], 2750 / 3
        )


if __name__ == "__main__":
    unittest.main()
