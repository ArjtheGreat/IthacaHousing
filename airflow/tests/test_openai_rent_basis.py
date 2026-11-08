"""Offline tests: AI evidence is gated before rent_per_person changes."""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))

from extractors.rent_basis_openai import _source_records, _verbatim_evidence
from extractors.extract_rental_data import extract_rental_data


def rows():
    return pd.DataFrame([
        {
            "ListingId": "237571-30678009",
            "PropertyId": "237571",
            "ListingAddress": "121 Lake St",
            "Bedrooms": 2, "Bathrooms": 2, "RentAmount": 1600,
            "RentType": "Price Per Unit",
            "ShortDescription": "Private room: $1600 per person",
            "HousingType": "Rent", "UnitName": "Room A",
        },
        {
            "ListingId": "237571-30743209",
            "PropertyId": "237571",
            "ListingAddress": "121 Lake St",
            "Bedrooms": 2, "Bathrooms": 2, "RentAmount": 3700,
            "RentType": "Price Per Unit",
            "ShortDescription": "Conventional 2 bedroom apartment",
            "HousingType": "Rent", "UnitName": "Unit 104",
        },
    ])


class OpenAIRentBasisTests(unittest.TestCase):
    def test_quote_must_be_in_this_floorplan_or_property_description(self):
        records = _source_records(rows())
        self.assertTrue(_verbatim_evidence(
            "$1600 per person", records, "237571-30678009"
        ))
        self.assertFalse(_verbatim_evidence(
            "$1600 per person", records, "237571-30743209"
        ))
        self.assertFalse(_verbatim_evidence("2", records, "237571-30678009"))

    def test_accepted_override_updates_rent_per_person(self):
        def classifier(df):
            out = df.copy()
            out["rent_basis"] = ["per_person", "per_unit"]
            out["rent_basis_confidence"] = ["high", "high"]
            out["rent_basis_evidence"] = [
                "$1600 per person", "Conventional 2 bedroom apartment"
            ]
            out["rent_basis_evidence_type"] = ["explicit", "explicit"]
            out["rent_basis_source"] = "openai"
            return out

        with patch("extractors.extract_rental_data.classify_rent_bases", classifier):
            out = extract_rental_data(rows())
        self.assertEqual(out["rent_per_person"].tolist(), [1600.0, 1850.0])
        self.assertEqual(out["ithaca_insights_adjustment"].tolist(), [True, False])
        self.assertEqual(out["total_rent_amount"].tolist(), [3200.0, 3700.0])

    def test_uncertain_classification_never_changes_source_interpretation(self):
        def classifier(df):
            out = df.copy()
            out["rent_basis"] = ["per_person", "unknown"]
            out["rent_basis_confidence"] = ["medium", "low"]
            out["rent_basis_evidence"] = ["looks cheap", ""]
            out["rent_basis_evidence_type"] = ["inferred", "none"]
            out["rent_basis_source"] = "openai"
            return out

        with patch("extractors.extract_rental_data.classify_rent_bases", classifier):
            out = extract_rental_data(rows())
        self.assertEqual(out["rent_per_person"].tolist(), [800.0, 1850.0])
        self.assertFalse(out["ithaca_insights_adjustment"].any())


if __name__ == "__main__":
    unittest.main()
