"""Offline regression tests for no-repeat OpenAI rent-basis classification."""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from extractors.rent_basis_openai import (
    MODEL, _fingerprint, _source_records, classify_rent_bases,
)


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.frame = pd.DataFrame([
            {
                "ListingId": "7734-17722",
                "PropertyId": "7734",
                "ListingAddress": "143 Maple Ave",
                "RentType": "Price Per Unit",
                "RentAmount": 1240,
                "Bedrooms": 2,
                "Bathrooms": 1,
                "ShortDescription": "Individual leases, rent per bedroom",
                "UnitName": "2BR",
            },
        ])
        self.fingerprint = _fingerprint(_source_records(self.frame))
        self.cache = {
            "7734-17722": {
                "listingid": "7734-17722",
                "rent_basis": "per_person",
                "rent_basis_confidence": "high",
                "rent_basis_evidence": "rent per bedroom",
                "rent_basis_evidence_type": "explicit",
                "rent_basis_source": "openai",
                "rent_basis_fingerprint": self.fingerprint,
            }
        }

    def test_unchanged_property_uses_cache_without_api_key(self):
        with patch.dict(os.environ, {"RENT_BASIS_OPENAI_ENABLED": "1"}, clear=True):
            with patch(
                "extractors.rent_basis_openai._load_cached_results",
                return_value=self.cache,
            ):
                out = classify_rent_bases(self.frame)
        self.assertEqual(out.loc[0, "rent_basis"], "per_person")
        self.assertEqual(out.loc[0, "rent_basis_confidence"], "high")
        self.assertEqual(out.loc[0, "rent_basis_fingerprint"], self.fingerprint)

    def test_price_change_invalidates_cache(self):
        changed = self.frame.copy()
        changed.loc[0, "RentAmount"] = 1260
        new_hash = _fingerprint(_source_records(changed))
        self.assertNotEqual(self.fingerprint, new_hash)

    def test_unknown_is_cached_and_not_assumed_verified(self):
        cache = {
            "7734-17722": {
                **self.cache["7734-17722"],
                "rent_basis": "unknown",
                "rent_basis_confidence": "low",
                "rent_basis_evidence_type": "none",
                "rent_basis_evidence": "",
            }
        }
        with patch.dict(os.environ, {"RENT_BASIS_OPENAI_ENABLED": "1"}, clear=True):
            with patch(
                "extractors.rent_basis_openai._load_cached_results",
                return_value=cache,
            ):
                out = classify_rent_bases(self.frame)
        self.assertEqual(out.loc[0, "rent_basis"], "unknown")
        self.assertEqual(out.loc[0, "rent_basis_confidence"], "low")


if __name__ == "__main__":
    unittest.main()
