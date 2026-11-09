"""IQR-only rent-basis reconciliation against independently reviewed prices.

Do not use the rents being classified to establish their own reference bands.
All confirmed rows come from persistent rent_basis_reviews records loaded before
the ingest TRUNCATE. One-bedroom advertised prices are numerically unambiguous.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

IQR_MULTIPLIER = 1.5
MIN_REFERENCE_PROPERTIES = 8


def audit_normalized_rents(frame: pd.DataFrame) -> pd.DataFrame:
    """Choose a rent basis only when one hypothesis fits a verified IQR band.

    Reviewed rows are authoritative even if an IQR marks them unusual.
    Both/none plausible -> preserve baseline amount, mark unknown and review.
    No adequate verified reference -> preserve baseline, mark unknown and review.
    """
    out = frame.copy()
    advertised = pd.to_numeric(out["RentAmount"], errors="coerce")
    people = pd.to_numeric(out["num_people"], errors="coerce")
    initial_rent = pd.to_numeric(out["rent_per_person"], errors="coerce")
    known = out["rent_verification_status"].eq("source_verified") & out[
        "rent_basis"
    ].isin(["per_person", "per_unit"])
    valid = advertised.gt(0) & people.gt(0) & np.isfinite(advertised)
    bucket = people.clip(lower=1, upper=5).fillna(0).astype(int)
    property_id = (
        out["PropertyId"].astype(str)
        if "PropertyId" in out
        else out["ListingId"].astype(str).str.rsplit("-", n=1).str[0]
    )

    # A 1BR has the same mathematical rent/person under both hypotheses.
    # Its numeric price is suitable as a reference without asserting lease basis.
    one_bed_reference = valid & people.eq(1)
    reference = (known | one_bed_reference) & valid & initial_rent.gt(0)
    refs = pd.DataFrame({
        "bucket": bucket[reference],
        "property_id": property_id[reference],
        "rent": initial_rent[reference],
    })

    bounds = {}
    for group, records in refs.groupby("bucket"):
        per_property = records.groupby("property_id")["rent"].median()
        if len(per_property) < MIN_REFERENCE_PROPERTIES:
            continue
        log_rent = np.log(per_property)
        q1, q3 = log_rent.quantile([.25, .75])
        log_iqr = q3 - q1
        bounds[group] = (
            float(np.exp(q1 - IQR_MULTIPLIER * log_iqr)),
            float(np.exp(q3 + IQR_MULTIPLIER * log_iqr)),
        )

    lower = bucket.map({int(k): v[0] for k, v in bounds.items()})
    upper = bucket.map({int(k): v[1] for k, v in bounds.items()})
    has_reference = lower.notna() & upper.notna()
    per_unit = advertised.div(people.where(people.gt(0)))
    per_person = advertised.where(advertised.gt(0))
    unit_in = valid & has_reference & per_unit.ge(lower) & per_unit.le(upper)
    person_in = valid & has_reference & per_person.ge(lower) & per_person.le(upper)
    one_in = unit_in ^ person_in

    choose_person = ~known & one_in & person_in & people.gt(1)
    choose_unit = ~known & one_in & unit_in & people.gt(1)
    determined = choose_person | choose_unit
    old = initial_rent.copy()

    out.loc[choose_person, "rent_per_person"] = per_person[choose_person]
    out.loc[choose_person, "total_rent_amount"] = (
        advertised[choose_person] * people[choose_person]
    )
    out.loc[choose_unit, "rent_per_person"] = per_unit[choose_unit]
    out.loc[choose_unit, "total_rent_amount"] = advertised[choose_unit]

    out["rent_final_basis"] = "unknown"
    out.loc[known, "rent_final_basis"] = out.loc[known, "rent_basis"]
    out.loc[choose_person, "rent_final_basis"] = "per_person"
    out.loc[choose_unit, "rent_final_basis"] = "per_unit"
    out.loc[determined, "rent_basis"] = out.loc[determined, "rent_final_basis"]
    out.loc[determined, "rent_basis_source"] = "iqr_only"
    out.loc[determined, "rent_basis_confidence"] = "medium"
    out.loc[determined, "rent_basis_evidence_type"] = "inferred"

    new_rent = pd.to_numeric(out["rent_per_person"], errors="coerce")
    changed = determined & (
        ~np.isclose(old.fillna(-1), new_rent.fillna(-2), atol=.51, rtol=0)
    )
    out.loc[changed, "ithaca_insights_adjustment"] = True
    out.loc[changed, "suspected_landlord_pricing_error"] = True
    out.loc[changed & choose_person, "pricing_adjustment_reason"] = "iqr_unique_per_person"
    out.loc[changed & choose_unit, "pricing_adjustment_reason"] = "iqr_unique_per_unit"

    out["rent_iqr_lower_cutoff"] = lower
    out["rent_iqr_upper_cutoff"] = upper
    out["rent_iqr_reference_provisional"] = ~has_reference
    out["rent_iqr_low_outlier"] = (
        new_rent.gt(0) & has_reference & new_rent.lt(lower)
    )

    ambiguous = ~known & people.gt(1) & valid & unit_in & person_in
    neither = ~known & people.gt(1) & valid & has_reference & ~unit_in & ~person_in
    no_reference = ~known & people.gt(1) & valid & ~has_reference
    missing = ~valid
    numeric_one_bed = ~known & valid & people.eq(1)
    one_bed_outlier = numeric_one_bed & has_reference & (
        new_rent.lt(lower) | new_rent.gt(upper)
    )
    out["rent_review_reason"] = None
    out.loc[ambiguous, "rent_review_reason"] = "iqr_both_plausible"
    out.loc[neither, "rent_review_reason"] = "iqr_neither_plausible"
    out.loc[no_reference, "rent_review_reason"] = "iqr_insufficient_verified_reference"
    out.loc[missing, "rent_review_reason"] = "missing_rent_or_bedrooms"
    out.loc[one_bed_outlier, "rent_review_reason"] = "one_bed_iqr_outlier"
    out["rent_review_flag"] = out["rent_review_reason"].notna()

    out.loc[determined, "rent_verification_status"] = "iqr_selected_unverified"
    out.loc[~known & ~determined, "rent_verification_status"] = "review"
    out.loc[numeric_one_bed & ~one_bed_outlier, "rent_verification_status"] = (
        "plausible_unverified"
    )
    out.loc[known, "rent_verification_status"] = "source_verified"
    out.loc[known, "rent_review_flag"] = False
    out.loc[known, "rent_review_reason"] = None

    print(
        f"📊 Verified-only 1.5× log-IQR: groups={sorted(bounds)}, "
        f"verified={int(known.sum())}, changed={int(changed.sum())}, "
        f"unresolved={int(out['rent_final_basis'].eq('unknown').sum())}"
    )
    return out
