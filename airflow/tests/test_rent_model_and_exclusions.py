"""Unit-level exclusion and notebook model regression tests."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))

from core.excluded_listing_unit_ids import (
    EXCLUDED_LISTING_UNIT_IDS,
    exclude_listing_units,
)
from ml.model_training import define_X_Y_variables
from ml.comparative_market_analysis import perform_cma


class RentModelAndExclusionTests(unittest.TestCase):
    def test_rogue_lake_floorplan_is_excluded_but_siblings_survive(self):
        frame = pd.DataFrame({
            "ListingId": [
                "237571-30678009",
                "237571-30743208",
                "118390-30706572",
            ],
            "rent_per_person": [800, 1850, 588],
        })
        self.assertIn("237571-30678009", EXCLUDED_LISTING_UNIT_IDS)
        filtered = exclude_listing_units(frame)
        self.assertEqual(filtered["ListingId"].tolist(), [
            "237571-30743208", "118390-30706572",
        ])
        self.assertEqual(len(frame), 3)

    def test_lowercase_db_ids_also_supported(self):
        frame = pd.DataFrame({
            "listingid": ["237571-30678009", "237571-30743208"],
        })
        self.assertEqual(
            exclude_listing_units(frame)["listingid"].tolist(),
            ["237571-30743208"],
        )

    def test_cma_excludes_every_unit_from_subject_property(self):
        frame = pd.DataFrame({
            "ListingId": ["522-1", "522-2", "522-3", "110-1", "220-1"],
            "PropertyId": ["522", "522", "522", "110", "220"],
            "rent_per_person": [1125, 1150, 1175, 1425, 900],
        })
        X = pd.DataFrame({"feature": [0.0, 0.01, 0.02, 0.03, 0.04]})
        result = perform_cma(X, frame, n_neighbors=3)
        for _, row in result.iterrows():
            self.assertTrue(all(
                neighbor.split("-")[0] != row["PropertyId"]
                for neighbor in row["nearest_neighbor_listingIds"]
            ))
            self.assertEqual(len(row["nearest_neighbor_listingIds"]), 2)
            prices = dict(zip(result["ListingId"], result["rent_per_person"]))
            self.assertAlmostEqual(
                row["predicted_rent_cma"],
                np.mean([prices[neighbor] for neighbor in row["nearest_neighbor_listingIds"]]),
            )

    def test_cma_with_only_one_property_has_no_comps(self):
        frame = pd.DataFrame({
            "ListingId": ["522-1", "522-2"],
            "PropertyId": ["522", "522"],
            "rent_per_person": [1125, 1150],
        })
        result = perform_cma(pd.DataFrame({"x": [1, 2]}), frame)
        self.assertTrue(all(not ids for ids in result["nearest_neighbor_listingIds"]))
        self.assertTrue(result["predicted_rent_cma"].isna().all())

    def test_notebook_predictors_include_separate_amenities(self):
        data = pd.DataFrame({
            "rent_per_person": [1100, 1900, 1500],
            "pets": [0, 1, 0],
            "combined_bedrooms_bathrooms": [2.5, 4.0, 2.5],
            "unit_sqft": [450, np.nan, 900],
            "available_bedrooms": [1, 2, 1],
            "available_bathrooms": [1, 2, 1],
            "has_fitness_center": [0, 1, 0],
            "has_in_unit_laundry": [0, 1, 1],
            "per_person_leasing": [1, 0, 1],
            "latitude": [42.44, 42.45, 42.46],
            "longitude": [-76.49, -76.50, -76.51],
        })
        # Required amenity groups must be present on real pipeline frames;
        # create explicit zeros for the remaining flags here.
        from ml.model_training import (
            UNIT_AMENITIES, BUILDING_AMENITIES,
            UTILITY_AMENITIES, LEASING_AMENITIES,
        )
        for name in (
            *UNIT_AMENITIES, *BUILDING_AMENITIES,
            *UTILITY_AMENITIES, *LEASING_AMENITIES,
        ):
            if name not in data:
                data[name] = 0
        X, target = define_X_Y_variables(data)
        self.assertTrue({
            "has_fitness_center", "has_in_unit_laundry", "per_person_leasing",
            "unit_sqft", "available_bedrooms", "available_bathrooms",
        }.issubset(X.columns))
        self.assertNotIn("rent_per_person", X.columns)
        self.assertEqual(target.tolist(), [1100, 1900, 1500])


if __name__ == "__main__":
    unittest.main()
