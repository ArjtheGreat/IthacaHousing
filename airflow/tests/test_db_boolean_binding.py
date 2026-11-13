"""Ensure PostgreSQL boolean columns are not bound as numeric values."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from core.insert_into_postgredb import _as_postgres_boolean


class DatabaseBooleanTests(unittest.TestCase):
    def test_accepts_binary_numerics_and_native_booleans(self):
        for col in ("shared_facilities", "in_business_improvement_district",
                    "rent_manual_override"):
            for raw in (False, 0, 0.0, np.float64(0)):
                self.assertIs(_as_postgres_boolean(raw, col, "example"), False)
            for raw in (True, 1, 1.0, np.float64(1)):
                self.assertIs(_as_postgres_boolean(raw, col, "example"), True)

    def test_nulls_remain_null(self):
        for raw in (None, pd.NA, np.nan):
            self.assertIsNone(_as_postgres_boolean(
                raw, "in_business_improvement_district", "example"
            ))

    def test_invalid_values_fail_loudly(self):
        for raw in (2, 0.5, "no"):
            with self.assertRaisesRegex(ValueError, "in_business_improvement_district"):
                _as_postgres_boolean(raw, "in_business_improvement_district", "example")


if __name__ == "__main__":
    unittest.main()
