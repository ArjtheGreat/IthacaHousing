"""Post-LLM statistical audit and numerical quote consistency."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))

from extractors.rent_iqr_audit import audit_normalized_rents, check_quote_amounts, pre_classification_iqr_context
from extractors.rent_basis_openai import _source_records, _fingerprint
from extractors.extract_rental_data import extract_rental_data


def base_rows():
    # Enough verified observations to establish a stable reference.
    return pd.DataFrame({
        "rent_per_person": [1000.0] * 25 + [1100.0] * 25
        + [150.0, 1900.0],
        "rent_basis": ["per_person"] * 52,
        "rent_basis_confidence": ["high"] * 52,
        "rent_basis_evidence_type": ["explicit"] * 52,
        "rent_quote_amount_conflict": [False] * 52,
    })


class RentAuditTests(unittest.TestCase):
    def test_pre_iqr_provides_both_interpretations_without_changing_rent(self):
        frame = pd.DataFrame({
            "ListingId": [str(i) for i in range(50)] + ["candidate"],
            "PropertyId": [str(i) for i in range(50)] + ["candidate"],
            "RentAmount": [1100.0] * 50 + [1200.0],
            "num_people": [1.0] * 50 + [2.0],
            "rent_per_person": [1100.0] * 50 + [600.0],
            "Bedrooms": [1] * 50 + [2],
        })
        out = pre_classification_iqr_context(frame)
        self.assertEqual(out["rent_per_person"].tolist(), frame["rent_per_person"].tolist())
        candidate = out.iloc[-1]
        self.assertEqual(float(candidate["pre_iqr_per_unit_candidate"]), 600.0)
        self.assertEqual(float(candidate["pre_iqr_per_person_candidate"]), 1200.0)
        self.assertTrue(bool(candidate["pre_iqr_per_unit_candidate_below_cutoff"]))
        self.assertFalse(bool(candidate["pre_iqr_per_person_candidate_below_cutoff"]))

        records = _source_records(out.iloc[[-1]])
        diagnostics = records["floorplans"][0]["pre_iqr"]
        self.assertEqual(diagnostics["per_unit_candidate"], 600.0)
        self.assertEqual(diagnostics["per_person_candidate"], 1200.0)
        self.assertNotIn("renttype", str(records).lower())

    def test_diagnostic_changes_invalidate_cache_fingerprint(self):
        base = pd.DataFrame([{
            "ListingId": "one-1", "PropertyId": "one",
            "RentAmount": 1200, "Bedrooms": 2,
            "pre_iqr_lower_cutoff": 700.0,
            "pre_iqr_per_unit_candidate": 600,
            "pre_iqr_per_person_candidate": 1200,
            "pre_iqr_per_unit_candidate_below_cutoff": True,
            "pre_iqr_per_person_candidate_below_cutoff": False,
        }])
        changed = base.copy()
        changed["pre_iqr_lower_cutoff"] = 550.0
        changed["pre_iqr_per_unit_candidate_below_cutoff"] = False
        self.assertNotEqual(_fingerprint(_source_records(base)),
                            _fingerprint(_source_records(changed)))

    def test_low_tail_flags_without_changing_target(self):
        original = base_rows()
        result = audit_normalized_rents(original)
        self.assertEqual(result["rent_per_person"].tolist(),
                         original["rent_per_person"].tolist())
        self.assertTrue(result.loc[50, "rent_iqr_low_outlier"])
        self.assertFalse(result.loc[51, "rent_iqr_low_outlier"])
        self.assertTrue(result.loc[50, "rent_review_flag"])
        self.assertTrue(result.loc[50, "rent_verification_status"] == "source_verified")

    def test_unverified_low_rent_is_review(self):
        frame = base_rows()
        frame.loc[50, "rent_basis_evidence_type"] = "inferred"
        result = audit_normalized_rents(frame)
        self.assertEqual(result.loc[50, "rent_verification_status"], "review")

    def test_111_blair_dollar_quote_prevents_wrong_override(self):
        rows = pd.DataFrame([{
            "ListingId": "241613-30747112",
            "PropertyId": "241613",
            "RentAmount": 1850,
            "RentType": "Price Per Unit",
            "Bedrooms": 2,
            "Bathrooms": 1,
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
            result = extract_rental_data(rows)
        self.assertEqual(float(result.loc[0, "rent_per_person"]), 925.0)
        self.assertTrue(result.loc[0, "rent_quote_amount_conflict"])
        self.assertTrue(result.loc[0, "rent_review_flag"])
        self.assertEqual(result.loc[0, "rent_verification_status"], "review")
        self.assertFalse(result.loc[0, "ithaca_insights_adjustment"])

    def test_quote_matching_original_rent_is_not_conflict(self):
        frame = pd.DataFrame([{
            "RentAmount": 1000.0,
            "rent_basis_confidence": "high",
            "rent_basis_evidence_type": "explicit",
            "rent_basis_evidence": "Rent is $1,000 per room, per month",
        }])
        self.assertFalse(bool(check_quote_amounts(frame).iloc[0]))

    def test_no_automatic_flip_for_unknown_low_rent(self):
        frame = base_rows()
        frame.loc[50, ["rent_basis", "rent_basis_confidence",
                       "rent_basis_evidence_type"]] = ["unknown", "low", "none"]
        result = audit_normalized_rents(frame)
        self.assertEqual(float(result.loc[50, "rent_per_person"]), 150.0)
        self.assertEqual(result.loc[50, "rent_verification_status"], "review")

    def test_empty_reference_is_safe(self):
        frame = base_rows().iloc[:0]
        result = audit_normalized_rents(frame)
        self.assertTrue(result.empty)


if __name__ == "__main__":
    unittest.main()
