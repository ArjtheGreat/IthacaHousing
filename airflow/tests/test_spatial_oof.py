"""Regression tests for the spatial challenger and property-excluded comparable rents."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from ml.archive.spatial_oof import compute_fair_rent_oof_spatial
from ml.archive.spatial_features import add_spatial_fold_features


class SpatialOOFTests(unittest.TestCase):
    def _frame(self):
        rows = []
        for property_no in range(12):
            for unit in range(2):
                rows.append({
                    "PropertyId": str(property_no),
                    "ListingId": f"{property_no}-{unit}",
                    "latitude": 42.43 + property_no * 0.002,
                    "longitude": -76.51 + property_no * 0.002,
                    "x_meters": property_no * 20.0,
                    "y_meters": property_no * 25.0,
                    "YR_BUILT_ENCODED": 1980 + property_no,
                    "combined_bedrooms_bathrooms": 2 + (property_no % 3),
                    "rent_per_person": 800 + property_no * 35 + unit * 5,
                })
        return pd.DataFrame(rows)

    def test_spatial_oof_outputs_same_metrics_as_baseline(self):
        frame = self._frame()
        out, fold_metrics, overall, importance = compute_fair_rent_oof_spatial(
            frame,
            np.log(frame["rent_per_person"].to_numpy()),
            ["YR_BUILT_ENCODED", "combined_bedrooms_bathrooms",
             "x_meters", "y_meters"],
            n_splits=3,
            n_estimators=12,
            max_depth=2,
        )
        self.assertEqual(len(out), len(frame))
        self.assertEqual(int(fold_metrics.test_listings.sum()), len(frame))
        self.assertTrue(np.isfinite(out["fair_rent"]).all())
        self.assertAlmostEqual(
            overall["rmse"],
            float(np.sqrt(np.mean((out["actual_rent"] - out["fair_rent"]) ** 2))),
        )
        features = set(importance["feature"])
        self.assertIn("knn_rent_log", features)
        self.assertIn("h3_7_te", features)
        self.assertIn("latitude", features)
        self.assertIn("longitude", features)
        self.assertNotIn("x_meters", features)
        self.assertNotIn("y_meters", features)

    def test_train_spatial_lags_never_see_their_own_property(self):
        frame = self._frame()
        train = frame.loc[frame["PropertyId"].isin(["0", "1", "2"])].copy()
        test = frame.loc[frame["PropertyId"] == "3"].copy()
        y = np.log(train["rent_per_person"].to_numpy())
        tr1, te1 = add_spatial_fold_features(train, test, y, k=3)

        # Reprice property 0 dramatically: none of its own training features
        # should change, but others can legitimately change.
        y2 = y.copy()
        y2[train["PropertyId"].to_numpy() == "0"] += 3.0
        tr2, te2 = add_spatial_fold_features(train, test, y2, k=3)
        own = train["PropertyId"] == "0"
        for name in ("knn_rent_log", "h3_6_te", "h3_7_te"):
            np.testing.assert_allclose(
                tr1.loc[own, name], tr2.loc[own, name], equal_nan=True,
            )
        self.assertFalse(
            np.allclose(te1["knn_rent_log"], te2["knn_rent_log"])
        )


if __name__ == "__main__":
    unittest.main()
