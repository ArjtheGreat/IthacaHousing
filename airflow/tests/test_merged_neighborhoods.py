"""Regression tests for James Spokes' merged Ithaca neighborhoods."""
import sys
import unittest
from pathlib import Path

import geopandas as gpd
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from extractors.extract_rental_data import extract_neighborhood, geojson_path


class NeighborhoodGeometryTests(unittest.TestCase):
    def test_merged_source_has_20_polygons_and_19_names(self):
        frame = gpd.read_file(geojson_path)
        self.assertEqual(len(frame), 20)
        self.assertEqual(frame["name"].nunique(), 19)
        self.assertEqual((frame["name"] == "West End").sum(), 2)

    def test_representative_points_assign_expected_names_without_duplication(self):
        neighborhoods = gpd.read_file(geojson_path).to_crs("EPSG:4326")
        rows = []
        for pos, item in neighborhoods.reset_index(drop=True).iterrows():
            pt = item.geometry.representative_point()
            rows.append({
                "PropertyId": f"property-{pos}",
                "ListingAddress": f"property-{pos}",
                "latitude": pt.y,
                "longitude": pt.x,
            })
        rows.append({
            "PropertyId": "out-of-town",
            "ListingAddress": "out-of-town",
            "latitude": 42.55,
            "longitude": -76.40,
        })
        source = pd.DataFrame(rows)
        found = extract_neighborhood(source)
        self.assertEqual(len(found), len(source))
        self.assertTrue(found.iloc[:20]["neighborhood"].notna().all())
        self.assertTrue(pd.isna(found.iloc[20]["neighborhood"]))
        self.assertGreaterEqual(found["neighborhood"].nunique(), 17)


if __name__ == "__main__":
    unittest.main()
