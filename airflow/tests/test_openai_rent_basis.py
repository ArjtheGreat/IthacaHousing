"""Offline tests of source-grounded rent basis classification and normalization."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))

from extractors.rent_basis_openai import (
    _source_records,
    validate_explicit_evidence,
    _fingerprint,
)
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


def entry(listingid, quote, source, basis="per_person"):
    return {
        "listingid": listingid, "rent_basis": basis,
        "evidence": quote, "evidence_source": source,
    }


class OpenAIRentBasisTests(unittest.TestCase):
    def test_cornell_rent_type_not_sent_to_ai(self):
        records = _source_records(rows())
        self.assertNotIn("property_rent_type", records["property"])
        self.assertNotIn("RentType", str(records))
        changed = rows()
        changed["RentType"] = "Price per Person"
        self.assertEqual(_fingerprint(_source_records(rows())),
                         _fingerprint(_source_records(changed)))

    def test_quote_must_be_from_the_correct_floorplan_field(self):
        records = _source_records(rows())
        self.assertTrue(validate_explicit_evidence(
            entry("237571-30678009", "$1600 per person", "source_description"),
            records,
        ))
        self.assertFalse(validate_explicit_evidence(
            entry("237571-30743209", "$1600 per person", "source_description"),
            records,
        ))
        self.assertFalse(validate_explicit_evidence(
            entry("237571-30678009", "Rent is $1600 per person", "source_description"),
            records,
        ))
        self.assertFalse(validate_explicit_evidence(
            entry("237571-30678009", "$1600 per person", "unit_name"),
            records,
        ))

    def test_fairview_qualified_property_statement(self):
        frame = rows().copy()
        frame["ShortDescription"] = (
            "Two and three bedroom unit pricing is listed by bed, "
            "however you will be responsible for finding roommates."
        )
        frame["Bedrooms"] = [2, 1]
        records = _source_records(frame)
        quote = "Two and three bedroom unit pricing is listed by bed"
        self.assertTrue(validate_explicit_evidence(
            entry("237571-30678009", quote, "property_description"), records,
        ))
        self.assertFalse(validate_explicit_evidence(
            entry("237571-30743209", quote, "property_description"), records,
        ))

    def test_by_the_bed_floorplan_title(self):
        frame = rows()
        frame.loc[0, "UnitName"] = "6x2 - By The Bed Rent Price"
        records = _source_records(frame)
        self.assertTrue(validate_explicit_evidence(
            entry("237571-30678009", "By The Bed Rent Price", "unit_name"),
            records,
        ))

    def test_individual_leases_alone_not_explicit(self):
        frame = rows()
        frame.loc[0, "UnitName"] = "Individual Leases Offered"
        records = _source_records(frame)
        self.assertFalse(validate_explicit_evidence(
            entry("237571-30678009", "Individual Leases Offered", "unit_name"),
            records,
        ))

    def test_accepted_override_updates_rent_per_person(self):
        def classifier(df):
            out = df.copy()
            out["rent_basis"] = ["per_person", "per_unit"]
            out["rent_basis_confidence"] = ["high", "high"]
            out["rent_basis_evidence"] = [
                "$1600 per person", "Conventional 2 bedroom apartment"
            ]
            out["rent_basis_evidence_type"] = ["explicit", "inferred"]
            out["rent_basis_evidence_field"] = ["source_description", "none"]
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
            out["rent_basis_evidence_field"] = ["none", "none"]
            out["rent_basis_source"] = "openai"
            return out

        with patch("extractors.extract_rental_data.classify_rent_bases", classifier):
            out = extract_rental_data(rows())
        self.assertEqual(out["rent_per_person"].tolist(), [800.0, 1850.0])
        self.assertFalse(out["ithaca_insights_adjustment"].any())


if __name__ == "__main__":
    unittest.main()
