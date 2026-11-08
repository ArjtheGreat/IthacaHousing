"""Checks unit-size propagation without confusing it with parcel acreage."""
import unittest
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))

from core.fetch_housing_data import COLUMNS, rows_from_data
from ml.backfill_unit_sqft import build_backfill_rows
from ml.model_training import define_X_Y_variables


class UnitSquareFootageTests(unittest.TestCase):
    @staticmethod
    def source_data():
        return {
            "100": {
                "id": "100",
                "address": "1 Example St, Ithaca, NY 14850",
                "floorplans": [
                    {"id": 11, "bed": 1, "bath": 1, "min_rent": 1250, "sq_footage": "746"},
                    {"id": 12, "bed": 3, "bath": 2, "min_rent": 3300, "sq_footage": "1,204"},
                    {"id": 13, "bed": 2, "bath": 1, "min_rent": 2000, "sq_footage": None},
                    {"id": 14, "bed": 2, "bath": 1, "min_rent": 2000, "sq_footage": "0"},
                ],
            }
        }

    def test_source_export_keeps_unit_sqft(self):
        rows = rows_from_data(self.source_data())
        self.assertIn("unit_sqft", COLUMNS)
        self.assertEqual(rows[0]["unit_sqft"], 746)
        self.assertEqual(rows[1]["unit_sqft"], 1204)
        self.assertIsNone(rows[2]["unit_sqft"])

    def test_backfill_uses_stable_listing_ids_only_for_positive_areas(self):
        rows = rows_from_data(self.source_data())
        records = build_backfill_rows(rows)
        self.assertEqual(records, [
            {"listingid": "100-11", "unit_sqft": 746.0},
            {"listingid": "100-12", "unit_sqft": 1204.0},
        ])

    def test_model_keeps_unit_sqft_separate_from_assessment(self):
        rows = pd.DataFrame([
            {"rent_per_person": 1200, "unit_sqft": 746, "assessment_sqft": 5000,
             "walk_time_urishall": 10},
            {"rent_per_person": 900, "unit_sqft": None, "assessment_sqft": 5000,
             "walk_time_urishall": 15},
        ])
        X, y = define_X_Y_variables(rows)
        self.assertIn("unit_sqft", X.columns)
        self.assertTrue(pd.isna(X.loc[1, "unit_sqft"]))
        self.assertEqual(X.loc[0, "unit_sqft"], 746)
        self.assertEqual(y.tolist(), [1200, 900])


if __name__ == "__main__":
    unittest.main()
