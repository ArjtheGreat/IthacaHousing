"""Regression tests for the 2022 City of Ithaca ward category."""
import sys
import unittest
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))

from extractors.assign_wards import WARD_FILE, assign_wards, add_ward_indicators


class WardCategoryTests(unittest.TestCase):
    def test_ward_geometries_match_original_five_wards(self):
        wards = gpd.read_file(WARD_FILE)
        self.assertEqual(set(wards["WardNum"].astype(int)), set(range(1, 6)))
        self.assertEqual(len(wards), 5)

    def test_assigns_every_ward_and_preserves_outside_and_unit_rows(self):
        wards = gpd.read_file(WARD_FILE).to_crs("EPSG:4326")
        rows = []
        for row in wards.itertuples():
            point = row.geometry.representative_point()
            rows.append({
                "PropertyId": f"property-{row.WardNum}",
                "ListingId": f"property-{row.WardNum}-unit",
                "latitude": point.y,
                "longitude": point.x,
            })
        rows.append({
            "PropertyId": "outside",
            "ListingId": "outside-unit",
            "latitude": 42.55,
            "longitude": -76.40,
        })
        # Another unit at the same property should stay in the same ward.
        rows.append({**rows[0], "ListingId": "property-1-unit2"})
        source = pd.DataFrame(rows)
        result = assign_wards(source)
        self.assertEqual(len(result), len(source))
        self.assertEqual(result.loc[:4, "ward"].tolist(), [
            f"Ward {n}" for n in wards["WardNum"].astype(int)
        ])
        self.assertTrue(pd.isna(result.loc[5, "ward"]))
        self.assertEqual(result.loc[6, "ward"], result.loc[0, "ward"])

        encoded = add_ward_indicators(result)
        for n in range(1, 6):
            col = f"ward_{n}"
            self.assertEqual(int(encoded.loc[n - 1, col]), n == int(wards.iloc[n - 1].WardNum))
            self.assertTrue(np.isnan(encoded.loc[5, col]))

    def test_missing_coordinates_stay_unassigned(self):
        source = pd.DataFrame({
            "latitude": [np.nan, 42.55],
            "longitude": [-76.49, np.nan],
        })
        result = assign_wards(source)
        self.assertTrue(result["ward"].isna().all())


if __name__ == "__main__":
    unittest.main()
