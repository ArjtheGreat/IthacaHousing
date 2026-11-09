"""Regression tests for persisted rent reviews and IQR-only reconciliation."""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from extractors.rent_iqr_audit import audit_normalized_rents
from extractors.extract_rental_data import extract_rental_data


def base_reference():
    rows = []
    for i in range(24):
        price = 900 + i * 13
        rows.append({
            "ListingId": f"ref{i}-1", "RentAmount": price,
            "Bedrooms": 2, "num_people": 2,
            "rent_per_person": price, "total_rent_amount": price * 2,
            "rent_basis": "per_person",
            "rent_verification_status": "source_verified",
            "RentType": "Price Per Unit", "ithaca_insights_adjustment": True,
            "pricing_adjustment_reason": "reviewed_source_verified_per_person",
            "suspected_landlord_pricing_error": False,
        })
    return pd.DataFrame(rows)


class IQRTests(unittest.TestCase):
    def test_confirmed_reference_resolves_bad_unit_fallback(self):
        df = base_reference()
        candidate = pd.DataFrame([{
            "ListingId": "candidate-1", "RentAmount": 1050,
            "Bedrooms": 2, "num_people": 2,
            "rent_per_person": 525, "total_rent_amount": 1050,
            "rent_basis": "unknown", "rent_verification_status": "review",
            "RentType": "Price Per Unit", "ithaca_insights_adjustment": False,
            "pricing_adjustment_reason": None,
            "suspected_landlord_pricing_error": False,
        }])
        out = audit_normalized_rents(pd.concat([df, candidate], ignore_index=True))
        row = out.iloc[-1]
        self.assertEqual(float(row["rent_per_person"]), 1050)
        self.assertEqual(row["rent_final_basis"], "per_person")
        self.assertEqual(row["rent_verification_status"], "iqr_selected_unverified")

    def test_confirmed_is_never_demoted_to_unknown(self):
        df = base_reference()
        result = audit_normalized_rents(df)
        self.assertTrue(result["rent_final_basis"].eq("per_person").all())
        self.assertTrue(result["rent_verification_status"].eq("source_verified").all())

    def test_reference_count_is_unique_properties_not_listings(self):
        df = base_reference().copy()
        df["ListingId"] = [f"one-{i}" for i in range(len(df))]
        unknown = pd.DataFrame([{
            "ListingId": "candidate-1", "RentAmount": 1100,
            "Bedrooms": 2, "num_people": 2,
            "rent_per_person": 550, "total_rent_amount": 1100,
            "rent_basis": "unknown", "rent_verification_status": "review",
            "RentType": "Price Per Unit", "ithaca_insights_adjustment": False,
            "pricing_adjustment_reason": None,
            "suspected_landlord_pricing_error": False,
        }])
        out = audit_normalized_rents(pd.concat([df, unknown], ignore_index=True))
        row = out.iloc[-1]
        self.assertEqual(row["rent_final_basis"], "unknown")
        self.assertEqual(row["rent_review_reason"], "iqr_insufficient_verified_reference")
        self.assertEqual(float(row["rent_per_person"]), 550)

    def test_persistent_review_survives_without_llm(self):
        frame = pd.DataFrame([{
            "ListingId": "239596-30712107",
            "RentAmount": 900, "Bedrooms": 6,
            "Bathrooms": 2, "RentType": "Price Per Unit",
        }, {
            "ListingId": "building-1",
            "RentAmount": 1150, "Bedrooms": 16,
            "Bathrooms": 8, "RentType": "Price Per Unit",
        }])
        reviews = {
            "239596-30712107": {
                "source_rentamount": 900, "source_bedrooms": 6,
                "confirmed_basis": "per_person", "review_status": "confirmed",
                "evidence": "By-The-Bed 6 Bed $900",
            },
            "building-1": {
                "source_rentamount": 1150, "source_bedrooms": 16,
                "confirmed_basis": None, "review_status": "needs_review",
                "evidence": "building-wide total",
            },
        }
        with patch("extractors.extract_rental_data.load_rent_basis_reviews",
                   return_value=reviews):
            result = extract_rental_data(frame)
        self.assertEqual(float(result.iloc[0]["rent_per_person"]), 900)
        self.assertEqual(result.iloc[0]["rent_final_basis"], "per_person")
        self.assertEqual(result.iloc[0]["rent_verification_status"], "source_verified")
        self.assertTrue(pd.isna(result.iloc[1]["rent_per_person"]))
        self.assertEqual(result.iloc[1]["rent_review_reason"], "bedrooms_may_be_building_total")

    def test_price_change_invalidates_review(self):
        frame = pd.DataFrame([{
            "ListingId": "review-1", "RentAmount": 1250,
            "Bedrooms": 2, "Bathrooms": 1, "RentType": "Price Per Unit",
        }])
        with patch("extractors.extract_rental_data.load_rent_basis_reviews",
                   return_value={
                    "review-1": {"source_rentamount": 1000,
                                 "source_bedrooms": 2,
                                 "review_status": "confirmed",
                                 "confirmed_basis": "per_person",
                                 "evidence": "by bed"}
                   }):
            result = extract_rental_data(frame)
        self.assertNotEqual(result.iloc[0]["rent_verification_status"], "source_verified")
        self.assertEqual(result.iloc[0]["rent_per_person"], 625)


if __name__ == "__main__":
    unittest.main()
