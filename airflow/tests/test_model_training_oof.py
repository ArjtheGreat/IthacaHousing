"""Regression tests for the single-model, property-grouped OOF rent workflow."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from ml.model_training import compute_fair_rent_oof, define_X_Y_variables


class OOFModelTests(unittest.TestCase):
    def test_grouped_oof_returns_predictions_dollar_metrics_and_importance(self):
        rows = []
        for prop in range(12):
            for unit in range(2):
                rows.append({
                    "PropertyId": str(prop), "ListingId": f"{prop}-{unit}",
                    "latitude": 42.43 + prop * 0.001,
                    "longitude": -76.51 + prop * 0.001,
                    "combined_bedrooms_bathrooms": 2 + (prop % 4),
                    "walk_time_urishall": 8 + prop,
                    "rent_per_person": 700 + prop * 30 + unit * 10,
                })
        df = pd.DataFrame(rows)
        X, raw_y = define_X_Y_variables(df)
        out, folds, overall, importance = compute_fair_rent_oof(
            df, np.log(raw_y), list(X.columns),
            n_splits=3, n_estimators=12, max_depth=2,
        )
        self.assertEqual(len(out), len(df))
        self.assertTrue(out["fair_rent"].gt(0).all())
        self.assertEqual(len(folds), 3)
        self.assertEqual(set(folds["fold"]), {1, 2, 3})
        self.assertEqual(int(folds["test_listings"].sum()), len(df))
        self.assertAlmostEqual(
            overall["rmse"],
            np.sqrt(np.mean((out["actual_rent"] - out["fair_rent"]) ** 2)),
            places=5,
        )
        self.assertAlmostEqual(
            overall["bias"], (out["actual_rent"] - out["fair_rent"]).mean(),
            places=5,
        )
        self.assertFalse(importance.empty)
        self.assertIn("mean_normalized_gain", importance.columns)
        self.assertTrue(
            np.allclose(out["mispricing"], out["actual_rent"] - out["fair_rent"])
        )

    def test_target_derived_features_are_never_selected(self):
        df = pd.DataFrame({
            "PropertyId": ["a", "b", "c", "d"],
            "rent_per_person": [900., 950., 1100., 1150.],
            "log_rent": [6., 6., 7., 7.],
            "latitude": [42.43, 42.44, 42.45, 42.46],
            "longitude": [-76.5, -76.51, -76.52, -76.53],
            "walk_time_urishall": [7., 9., 11., 13.],
        })
        _, _, _, imp = compute_fair_rent_oof(
            df, np.log(df["rent_per_person"]),
            ["walk_time_urishall", "rent_per_person", "log_rent"],
            n_splits=2, n_estimators=5, max_depth=2,
        )
        self.assertNotIn("rent_per_person", imp["feature"].tolist())
        self.assertNotIn("log_rent", imp["feature"].tolist())

    def test_requires_multiple_properties(self):
        df = pd.DataFrame({
            "PropertyId": ["same", "same"],
            "latitude": [42.4, 42.4], "longitude": [-76.5, -76.5],
            "walk_time_urishall": [5., 6.],
        })
        with self.assertRaises(ValueError):
            compute_fair_rent_oof(
                df, np.log([900., 1000.]), ["walk_time_urishall"]
            )


if __name__ == "__main__":
    unittest.main()
