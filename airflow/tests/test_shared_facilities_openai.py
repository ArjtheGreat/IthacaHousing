"""Regression checks for unit-level cached GPT shared-facilities labels."""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from extractors import shared_facilities_openai as classifier


class SharedFacilitiesCacheTests(unittest.TestCase):
    def test_distinct_floorplans_have_distinct_evidence(self):
        a = pd.Series({
            "ListingId": "p-101", "UnitName": "A: private apartment",
            "Bedrooms": 1, "ShortDescription": "Mix of rooms and apartments",
        })
        b = pd.Series({
            "ListingId": "p-102", "UnitName": "B: room with communal kitchen",
            "Bedrooms": 1, "ShortDescription": "Mix of rooms and apartments",
        })
        self.assertNotEqual(
            classifier._fingerprint(classifier._evidence(a)),
            classifier._fingerprint(classifier._evidence(b)),
        )

    def test_modified_floorplan_invalidates_cache(self):
        row = pd.Series({
            "ListingId": "p-101", "UnitName": "Room 1", "Bedrooms": 1,
        })
        original = classifier._fingerprint(classifier._evidence(row))
        row["UnitName"] = "Self-contained Unit 1"
        modified = classifier._fingerprint(classifier._evidence(row))
        self.assertNotEqual(original, modified)

    def test_cached_units_make_no_api_calls(self):
        frame = pd.DataFrame([
            {"ListingId": "p-101", "Bedrooms": 1, "UnitName": "Room A"},
            {"ListingId": "p-102", "Bedrooms": 0, "UnitName": "Studio B"},
        ])
        cache = {}
        for _, row in frame.iterrows():
            listingid = row["ListingId"]
            cache[listingid] = {
                "listingid": listingid,
                "evidence_fingerprint": classifier._fingerprint(
                    classifier._evidence(row)
                ),
                "classification": "shared" if listingid == "p-101" else "unknown",
                "confidence": "high" if listingid == "p-101" else "low",
                "evidence": "Explicitly shared kitchen" if listingid == "p-101"
                            else "No unit-level information",
                "evidence_field": "UnitName",
                "physical_bedrooms": row["Bedrooms"],
            }
        engine = MagicMock()
        with patch.dict(os.environ, {"DB_URI": "postgresql://not-used"}, clear=False), \
             patch.object(classifier, "create_engine", return_value=engine), \
             patch.object(classifier, "_load_cache", return_value=cache), \
             patch.object(classifier, "_save_batch") as save:
            out = classifier.classify_shared_facilities(frame)
        self.assertIs(out.loc[0, "shared_facilities"], True)
        self.assertIsNone(out.loc[1, "shared_facilities"])
        self.assertEqual(out.loc[1, "physical_bedrooms"], 0)
        save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
