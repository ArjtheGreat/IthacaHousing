"""Tests for refreshed Cornell contacts and persisted property enrichment reuse."""
import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from core.fetch_housing_data import rows_from_data
from core.property_level import apply_cached_property_enrichment


class ContactAndCacheTests(unittest.TestCase):
    def test_cornell_contacts_are_copied_to_every_floorplan(self):
        data = {
            "10": {
                "id": 10,
                "address": "123 Blair St, Ithaca, NY 14850",
                "landlord_email": "leasing@example.com",
                "landlord_name": "",
                "full_name": "Test Manager",
                "landlord_username": "test-account",
                "contact_number": "(607) 555-0000",
                "floorplans": [
                    {"id": 1, "bed": 3, "bath": 1, "min_rent": "1360"},
                    {"id": 2, "bed": 2, "bath": 1, "min_rent": "1200"},
                ],
            }
        }
        result = rows_from_data(data)
        self.assertEqual(len(result), 2)
        for row in result:
            self.assertEqual(row["landlord_email"], "leasing@example.com")
            self.assertEqual(row["landlord_name"], "Test Manager")
            self.assertEqual(row["landlord_full_name"], "Test Manager")
            self.assertEqual(row["landlord_username"], "test-account")
            self.assertEqual(row["contact_number"], "(607) 555-0000")

    def test_known_properties_are_not_recomputed(self):
        source = pd.DataFrame([
            {"PropertyId": "10", "ListingId": "10-1", "landlord_email": "new@example.com"},
            {"PropertyId": "10", "ListingId": "10-2", "landlord_email": "new@example.com"},
            {"PropertyId": "20", "ListingId": "20-1", "landlord_email": "another@example.com"},
        ])
        existing = pd.DataFrame([
            {"listingid": "10-previous", "owner_name": "Cached Owner"}
        ])
        seen = []

        def compute(rep):
            seen.extend(rep["PropertyId"].tolist())
            result = rep.copy()
            result["owner_name"] = "Fresh Owner"
            return result

        result = apply_cached_property_enrichment(
            source, existing, compute, fields=["owner_name"],
            required=["owner_name"], label="test ownership",
        )
        self.assertEqual(seen, ["20"])
        assert_rows = result.set_index("ListingId")
        self.assertEqual(assert_rows.loc["10-1", "owner_name"], "Cached Owner")
        self.assertEqual(assert_rows.loc["10-2", "owner_name"], "Cached Owner")
        self.assertEqual(assert_rows.loc["20-1", "owner_name"], "Fresh Owner")
        self.assertEqual(assert_rows.loc["10-1", "landlord_email"], "new@example.com")

    def test_missing_cached_value_triggers_recomputation(self):
        source = pd.DataFrame([{"PropertyId": "10", "ListingId": "10-1"}])
        existing = pd.DataFrame([{"listingid": "10-old", "neighborhood": None}])
        calls = []

        def compute(rep):
            calls.append(1)
            rep = rep.copy()
            rep["neighborhood"] = "Collegetown"
            return rep

        result = apply_cached_property_enrichment(
            source, existing, compute, fields=["neighborhood"],
            required=["neighborhood"],
        )
        self.assertEqual(len(calls), 1)
        self.assertEqual(result.loc[0, "neighborhood"], "Collegetown")


if __name__ == "__main__":
    unittest.main()
