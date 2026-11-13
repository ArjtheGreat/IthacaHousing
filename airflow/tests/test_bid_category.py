"""Tests for official City of Ithaca BID classification; no network calls."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from shapely.geometry import Polygon

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from extractors.assign_bid import assign_bid


class BusinessImprovementDistrictTests(unittest.TestCase):
    def test_inside_outside_missing_and_boundary(self):
        polygon = Polygon([
            (-76.50, 42.43), (-76.48, 42.43),
            (-76.48, 42.45), (-76.50, 42.45),
        ])
        frame = pd.DataFrame({
            "PropertyId": ["a", "b", "c", "d", "a"],
            "latitude": [42.44, 42.46, None, 42.43, 42.44],
            "longitude": [-76.49, -76.49, -76.49, -76.49, -76.49],
        })
        with patch("extractors.assign_bid.load_bid_polygons", return_value=[polygon]):
            result = assign_bid(frame)

        self.assertEqual(len(result), len(frame))
        self.assertTrue(bool(result.loc[0, "in_business_improvement_district"]))
        self.assertFalse(bool(result.loc[1, "in_business_improvement_district"]))
        self.assertTrue(pd.isna(result.loc[2, "in_business_improvement_district"]))
        self.assertTrue(bool(result.loc[3, "in_business_improvement_district"]))
        self.assertEqual(
            result.loc[0, "in_business_improvement_district"],
            result.loc[4, "in_business_improvement_district"],
        )
        self.assertEqual(str(result["in_business_improvement_district"].dtype), "boolean")

    def test_gis_failure_cannot_falsely_mark_properties_outside(self):
        frame = pd.DataFrame({"latitude": [42.44], "longitude": [-76.49]})
        with patch("extractors.assign_bid.load_bid_polygons", side_effect=RuntimeError("offline")):
            with self.assertRaisesRegex(RuntimeError, "offline"):
                assign_bid(frame)


if __name__ == "__main__":
    unittest.main()
