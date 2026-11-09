"""Regression tests for the four-step rent basis pipeline."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from extractors.rent_iqr_audit import audit_normalized_rents, check_quote_amounts
from extractors.rent_basis_openai import _source_records
from extractors.extract_rental_data import extract_rental_data


def reference_frame():
    rows = []
    # Property-independent, credible 2BR rent/person reference distribution.
    for i in range(30):
        value = 950.0 + (i % 10) * 25.0
        rows.append({
            "ListingId": f"ref-{i}", "PropertyId": f"ref-{i}",
            "RentAmount": value, "RentType": "Price Per Person",
            "num_people": 2, "rent_per_person": value,
            "rent_basis": "per_person", "rent_basis_confidence": "medium",
            "rent_basis_evidence_type": "inferred",
            "rent_quote_amount_conflict": False,
        })
    return pd.DataFrame(rows)


def add_listing(frame, advertised, bedrooms=2, rent_type="Price Per Unit",
                basis="unknown", evidence_type="none", evidence=""):
    row = {
        "ListingId": "candidate-1", "PropertyId": "candidate",
        "RentAmount": advertised, "RentType": rent_type,
        "num_people": bedrooms,
        "rent_per_person": advertised / bedrooms
        if rent_type == "Price Per Unit" else advertised,
        "rent_basis": basis, "rent_basis_confidence":
        "high" if evidence_type == "explicit" else "low",
        "rent_basis_evidence_type": evidence_type,
        "rent_basis_evidence": evidence,
        "rent_quote_amount_conflict": False,
        "ithaca_insights_adjustment": False,
        "pricing_adjustment_reason": None,
        "total_rent_amount": advertised,
        "suspected_landlord_pricing_error": False,
    }
    return pd.concat([frame, pd.DataFrame([row])], ignore_index=True)


class BedroomIQRTests(unittest.TestCase):
    def test_one_plausible_person_corrects_rent_and_sets_final_basis(self):
        df = add_listing(reference_frame(), advertised=1050)
        out = audit_normalized_rents(df)
        candidate = out.iloc[-1]
        self.assertEqual(float(candidate["rent_per_person"]), 1050.0)
        self.assertEqual(candidate["rent_final_basis"], "per_person")
        self.assertEqual(candidate["pricing_adjustment_reason"], "iqr_unique_per_person")
        self.assertTrue(candidate["ithaca_insights_adjustment"])
        self.assertEqual(candidate["rent_verification_status"], "iqr_selected_unverified")
        self.assertEqual(candidate["rent_basis"], "unknown")  # preserve actual LLM cache

    def test_one_plausible_unit_keeps_correct_baseline_and_sets_basis(self):
        df = add_listing(reference_frame(), advertised=2100)
        out = audit_normalized_rents(df)
        candidate = out.iloc[-1]
        self.assertEqual(float(candidate["rent_per_person"]), 1050.0)
        self.assertEqual(candidate["rent_final_basis"], "per_unit")
        self.assertFalse(candidate["ithaca_insights_adjustment"])
        self.assertEqual(candidate["rent_verification_status"], "iqr_selected_unverified")

    def test_source_verified_price_overrides_iqr(self):
        df = add_listing(
            reference_frame(), advertised=1050, rent_type="Price Per Person",
            basis="per_person", evidence_type="explicit", evidence="pricing is per bed",
        )
        out = audit_normalized_rents(df)
        candidate = out.iloc[-1]
        self.assertEqual(float(candidate["rent_per_person"]), 1050.0)
        self.assertEqual(candidate["rent_verification_status"], "source_verified")
        self.assertFalse(candidate["ithaca_insights_adjustment"])

    def test_both_plausible_keep_original_and_flag_unknown(self):
        # Extremely broad reference quartiles make both 600 and 1200 plausible.
        df = reference_frame()
        df.loc[df.index[:10], "rent_per_person"] = 550.0
        df.loc[df.index[20:], "rent_per_person"] = 1550.0
        df = add_listing(df, advertised=1200)
        result = audit_normalized_rents(df).iloc[-1]
        self.assertEqual(float(result["rent_per_person"]), 600.0)
        self.assertEqual(result["rent_final_basis"], "unknown")
        self.assertTrue(result["rent_review_flag"])
        self.assertEqual(result["rent_review_reason"], "iqr_both_plausible")
        self.assertFalse(result["ithaca_insights_adjustment"])

    def test_neither_plausible_remains_for_review(self):
        df = add_listing(reference_frame(), advertised=10000)
        result = audit_normalized_rents(df).iloc[-1]
        self.assertEqual(float(result["rent_per_person"]), 5000.0)
        self.assertTrue(result["rent_review_flag"])
        self.assertEqual(result["rent_final_basis"], "unknown")

    def test_insufficient_properties_cannot_force_conversion(self):
        df = add_listing(reference_frame().iloc[:5], advertised=1000)
        result = audit_normalized_rents(df).iloc[-1]
        self.assertFalse(result["ithaca_insights_adjustment"])
        self.assertTrue(result["rent_iqr_reference_provisional"])
        self.assertEqual(result["rent_review_reason"], "iqr_insufficient_bedroom_reference")

    def test_111_blair_dollar_quote_prevents_wrong_override(self):
        row = pd.DataFrame([{
            "ListingId": "241613-30747112", "PropertyId": "241613",
            "RentAmount": 1850, "RentType": "Price Per Unit",
            "Bedrooms": 2, "Bathrooms": 1,
        }])
        def classifier(df):
            result = df.copy()
            result["rent_basis"] = "per_person"
            result["rent_basis_confidence"] = "high"
            result["rent_basis_evidence_type"] = "explicit"
            result["rent_basis_evidence"] = "only $925 per bedroom"
            result["rent_basis_source"] = "openai"
            return result
        with patch("extractors.extract_rental_data.classify_rent_bases", classifier):
            result = extract_rental_data(row).iloc[0]
        self.assertEqual(float(result["rent_per_person"]), 925.0)
        self.assertTrue(result["rent_quote_amount_conflict"])
        self.assertTrue(result["rent_review_flag"])
        self.assertFalse(result["ithaca_insights_adjustment"])

    def test_quotes_matching_advertised_amount_are_consistent(self):
        df = pd.DataFrame([{
            "RentAmount": 1000, "rent_basis_evidence_type": "explicit",
            "rent_basis_confidence": "high",
            "rent_basis_evidence": "Rent is $1,000 per room",
        }])
        self.assertFalse(bool(check_quote_amounts(df).iloc[0]))

    def test_llm_only_sees_original_listing_details(self):
        df = pd.DataFrame([{
            "ListingId": "1-2", "PropertyId": "1",
            "RentAmount": 1200, "Bedrooms": 2,
            "RentType": "Price Per Unit", "pre_iqr_lower_cutoff": 700,
        }])
        rec = _source_records(df)
        self.assertNotIn("pre_iqr", str(rec))
        self.assertNotIn("property_rent_type", str(rec))


if __name__ == "__main__":
    unittest.main()
