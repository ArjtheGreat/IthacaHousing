"""Tests for James Spokes' merged Ithaca neighborhood boundaries."""
import sys
import unittest
from pathlib import Path

import geopandas as gpd
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from extractors.extract_rental_data import extract_neighborhood, geojson_path


class NewNeighborhoodBoundariesTests(unittest.TestCase):
    def test_source_contains_all_named_regions(self):
        polygons = gpd.read_file(geojson_path)
        self.assertEqual(len(polygons), 20)
        self.assertEqual(polygons["name"].nunique(), 19)
        self.assertEqual((polygons["name"] == "West End").sum(), 2)

    def test_each_input_row_retained_even_if_polygons_overlap(self):
        polygons = gpd.read_file(geojson_path).to_crs("EPSG:4326")
        points = polygons.geometry.representative_point()
        listings = pd.DataFrame({
            "PropertyId": [str(i) for i in range(len(points))] + ["outside"],
            "latitude": points.y.tolist() + [42.60],
            "longitude": points.x.tolist() + [-76.25],
        })
        result = extract_neighborhood(listings)
        self.assertEqual(len(result), len(listings))
        self.assertTrue(result.loc[:len(points)-1, "neighborhood"].notna().all())
        self.assertTrue(pd.isna(result.loc[len(points), "neighborhood"]))


if __name__ == "__main__":
    unittest.main()
