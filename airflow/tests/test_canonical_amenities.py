"""Regressions for Cornell's overlapping amenity representations."""
import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from calculators.calculate_amenity_score import (
    CANONICAL_AMENITY_COLUMNS, add_canonical_amenities, extract_canonical_amenities,
)


class CanonicalAmenityTests(unittest.TestCase):
    def test_121_lake_features_are_not_confused_with_included_utilities(self):
        raw = [
            "Air Conditioning", "Central Heat and Air Conditioning",
            "Washer & Dryer", "Furnished Packages Available",
            "Internet Ready", "Fitness Center",
        ]
        got = extract_canonical_amenities(raw)
        self.assertEqual(got["has_ac"], 1)
        self.assertEqual(got["has_heating"], 1)
        self.assertEqual(got["has_in_unit_laundry"], 1)
        self.assertEqual(got["has_laundry"], 1)
        self.assertEqual(got["is_furnished"], 0)
        self.assertEqual(got["furnishing_option_available"], 1)
        self.assertEqual(got["internet_ready"], 1)
        self.assertEqual(got["internet_included_verified"], 0)
        self.assertEqual(got["heat_included_verified"], 0)
        self.assertEqual(got["has_fitness_center"], 1)

    def test_not_advertised_does_not_become_explicitly_included(self):
        got = extract_canonical_amenities(["WIFI", "Water", "Trash"])
        self.assertEqual(got["internet_available"], 1)
        self.assertEqual(got["water_advertised"], 1)
        self.assertEqual(got["trash_advertised"], 1)
        self.assertEqual(got["water_included_verified"], 0)
        self.assertEqual(got["internet_included_verified"], 0)

    def test_dataframe_and_json_array(self):
        frame = pd.DataFrame({"Amenities": [
            '["Heat Included", "Laundry On-Site"]',
            ["Washer & Dryer"],
        ]})
        out = add_canonical_amenities(frame)
        self.assertTrue(set(CANONICAL_AMENITY_COLUMNS).issubset(out.columns))
        self.assertEqual(out["heat_included_verified"].tolist(), [1, 0])
        self.assertEqual(out["has_shared_laundry"].tolist(), [1, 0])
        self.assertEqual(out["has_in_unit_laundry"].tolist(), [0, 1])
        self.assertEqual(out["has_laundry"].tolist(), [1, 1])


if __name__ == "__main__":
    unittest.main()
