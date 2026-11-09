"""Rent anomaly diagnostics before and after OpenAI price-basis classification.

The LLM determines what the advertised amount covers. This independent
lower-tail log-IQR audit only *flags* suspect values; it NEVER edits rents.
Retains the original 1.2*log-IQR threshold used by Ithaca Insights.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

LOG_IQR_MULTIPLIER = 1.5
MIN_REFERENCE_COUNT = 20


def pre_classification_iqr_context(frame: pd.DataFrame) -> pd.DataFrame:
    """Supply a *symmetric* IQR diagnostic before the LLM sees floorplans.

    Compute a provisional lower-tail log-IQR bound from the initial source-
    normalized rents. Show BOTH interpretations (advertised total / bedrooms
    and advertised per person), so we don't anchor the model to one hypothesis.
    This does not change amounts or create source verification.
    """
    out = frame.copy()
    baseline = pd.to_numeric(out["rent_per_person"], errors="coerce")
    original = pd.to_numeric(out["RentAmount"], errors="coerce")
    people = pd.to_numeric(out["num_people"], errors="coerce")
    reference = baseline.loc[baseline.notna() & np.isfinite(baseline) & baseline.gt(0)]
    if len(reference) >= 4:
        logged = np.log(reference)
        q25, q75 = logged.quantile([.25, .75])
        cutoff = float(np.exp(logged.median() - LOG_IQR_MULTIPLIER * (q75 - q25)))
    else:
        cutoff = np.nan

    candidate_unit = original.div(people.where(people.gt(0)))
    candidate_person = original.where(original.gt(0))
    for name, values in (
        ("pre_iqr_per_unit_candidate", candidate_unit),
        ("pre_iqr_per_person_candidate", candidate_person),
    ):
        out[name] = values.where(values.gt(0))
        out[name + "_below_cutoff"] = (
            (values.notna() & values.gt(0) & values.lt(cutoff))
            if np.isfinite(cutoff)
            else pd.Series(False, index=out.index)
        ).astype(bool)
    out["pre_iqr_lower_cutoff"] = cutoff if np.isfinite(cutoff) else np.nan
    print(
        "📊 Pre-LLM log-IQR (diagnostic only): "
        f"cutoff=${cutoff:,.0f}, "
        f"unit hypothesis low={int(out['pre_iqr_per_unit_candidate_below_cutoff'].sum())}, "
        f"person hypothesis low={int(out['pre_iqr_per_person_candidate_below_cutoff'].sum())}"
    )
    return out


def _quoted_amount(evidence):
    """Return a dollar-denominated amount quoted by a source, if unambiguous.

    The number in '$925 per bedroom' is NOT necessarily the same number as
    RentAmount=$1850, and must not trigger an automatic per-person override.
    """
    matches = re.findall(r"\$\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)", str(evidence or ""))
    if len(matches) != 1:
        return None
    return float(matches[0].replace(",", ""))


def check_quote_amounts(frame: pd.DataFrame) -> pd.Series:
    """Flag direct dollar quotes that contradict the advertised amount.

    Only checked for explicitly validated classifications. It does not treat
    absence of a dollar quote as evidence either way.
    """
    explicit = (
        frame["rent_basis_evidence_type"].eq("explicit")
        & frame["rent_basis_confidence"].eq("high")
    )
    raw = pd.to_numeric(frame["RentAmount"], errors="coerce")
    quoted = frame["rent_basis_evidence"].apply(_quoted_amount)
    quoted = pd.to_numeric(quoted, errors="coerce")
    return (explicit & quoted.notna() & raw.notna()
            & ~np.isclose(raw, quoted, rtol=0, atol=0.51))


def both_candidates_unresolved_mask(unit_in, person_in, has_bounds, valid, same):
    """Both plausible, neither plausible, or no reference: unresolved basis."""
    return valid & ~same & (
        (unit_in & person_in)
        | (has_bounds & ~unit_in & ~person_in)
        | ~has_bounds
    )


def audit_normalized_rents(frame: pd.DataFrame) -> pd.DataFrame:
    """Bedroom-stratified log-Tukey fences for both advertised-price hypotheses.

    This stage follows deterministic normalization and source-text LLM decisions.
    When exactly one candidate is within the IQR fence, prefer it unless
    independently verified source evidence contradicts the proposal.
    Both candidates within => keep the current value and flag as ambiguous.
    Neither within => preserve the price and flag review. Never treat IQR
    plausibility as source verification.
    """
    out = frame.copy()
    rents = pd.to_numeric(out["rent_per_person"], errors="coerce")
    advertised = pd.to_numeric(out["RentAmount"], errors="coerce")
    bedrooms = pd.to_numeric(out["num_people"], errors="coerce")
    valid = rents.gt(0) & np.isfinite(rents)
    explicit = (
        out["rent_basis_evidence_type"].eq("explicit")
        & out["rent_basis_confidence"].eq("high")
        & out["rent_basis"].isin(["per_person", "per_unit"])
    )
    conflict = out.get(
        "rent_quote_amount_conflict", pd.Series(False, index=out.index)
    ).fillna(False).astype(bool)

    # Property-level weighting prevents a 40-floorplan complex overwhelming
    # a five-property bedroom bucket. No source-verified-only restriction:
    # median/IQR are intentionally robust to limited contamination.
    property_ids = (
        out["PropertyId"].astype(str)
        if "PropertyId" in out.columns
        else out["ListingId"].astype(str).str.rsplit("-", n=1).str[0]
        if "ListingId" in out.columns
        else pd.Series(out.index.astype(str), index=out.index)
    )
    bedroom_group = bedrooms.clip(lower=1, upper=5).fillna(0).astype(int)
    refs = pd.DataFrame({
        "group": bedroom_group, "property": property_ids, "rent": rents,
    })
    refs = refs.loc[valid & bedroom_group.gt(0)].copy()

    bounds = {}
    for group, records in refs.groupby("group"):
        per_property = records.groupby("property")["rent"].median()
        if len(per_property) < MIN_REFERENCE_COUNT:
            continue
        logged = np.log(per_property)
        q1, q3 = logged.quantile([0.25, 0.75])
        iqr = q3 - q1
        bounds[group] = (
            float(np.exp(q1 - 1.5 * iqr)),
            float(np.exp(q3 + 1.5 * iqr)),
        )

    lower = bedroom_group.map({k: v[0] for k, v in bounds})
    upper = bedroom_group.map({k: v[1] for k, v in bounds})
    has_bounds = lower.notna() & upper.notna()
    unit_candidate = advertised.div(bedrooms.where(bedrooms.gt(0)))
    person_candidate = advertised.where(advertised.gt(0))

    def inside(candidate):
        return (
            has_bounds & candidate.notna() & np.isfinite(candidate)
            & candidate.ge(lower) & candidate.le(upper)
        )

    unit_in = inside(unit_candidate)
    person_in = inside(person_candidate)
    valid_candidates = (
        advertised.gt(0) & bedrooms.gt(0)
        & unit_candidate.notna() & person_candidate.notna()
    )
    same_candidate = np.isclose(
        unit_candidate.fillna(-1), person_candidate.fillna(-2),
        rtol=0, atol=0.01,
    )
    one_in = valid_candidates & ~same_candidate & (unit_in ^ person_in)

    # The LLM is an evidence extractor, not a market-price oracle. Explicit
    # verified price-basis quotes are stronger than population statistics.
    # A conflicting dollar quote also vetoes IQR auto-flips.
    supported = one_in & ~explicit & ~conflict
    choice_person = supported & person_in
    choice_unit = supported & unit_in

    raw_basis = out["RentType"].fillna("").astype(str).str.casefold()
    current_person = raw_basis.str.contains("person")
    current_person |= (
        out["ithaca_insights_adjustment"].fillna(False).astype(bool)
        & out["pricing_adjustment_reason"].eq("openai_source_verified_per_person")
    )
    current_person &= ~out["pricing_adjustment_reason"].eq("openai_source_verified_per_unit")

    # Do not label a statistic as "openai" or fabricate source evidence.
    changed_person = choice_person & ~current_person
    changed_unit = choice_unit & current_person
    out.loc[changed_person, "rent_per_person"] = person_candidate[changed_person]
    out.loc[changed_person, "total_rent_amount"] = (
        advertised[changed_person] * bedrooms[changed_person]
    )
    out.loc[changed_unit, "rent_per_person"] = unit_candidate[changed_unit]
    out.loc[changed_unit, "total_rent_amount"] = advertised[changed_unit]
    changed = changed_person | changed_unit
    out.loc[changed, "ithaca_insights_adjustment"] = True
    out.loc[changed, "suspected_landlord_pricing_error"] = True
    out.loc[changed_person, "pricing_adjustment_reason"] = "iqr_unique_per_person"
    out.loc[changed_unit, "pricing_adjustment_reason"] = "iqr_unique_per_unit"

    # Keep the raw LLM classification untouched so the fingerprint cache can
    # reuse genuine model outputs; rent_final_basis stores the reconciled result.
    # The final interpreted basis is tracked separately from what OpenAI said.
    # Existing rent_basis remains the LLM audit result, unchanged.
    out["rent_final_basis"] = np.where(current_person, "per_person", "per_unit")
    out.loc[choice_person, "rent_final_basis"] = "per_person"
    out.loc[choice_unit, "rent_final_basis"] = "per_unit"
    out.loc[~valid_candidates | both_candidates_unresolved_mask(unit_in, person_in, has_bounds, valid_candidates, same_candidate), "rent_final_basis"] = "unknown"
    out["rent_iqr_lower_cutoff"] = lower
    out["rent_iqr_upper_cutoff"] = upper
    out["rent_iqr_reference_provisional"] = ~has_bounds
    final_rents = pd.to_numeric(out["rent_per_person"], errors="coerce")
    out["rent_iqr_low_outlier"] = has_bounds & final_rents.gt(0) & final_rents.lt(lower)

    both_in = valid_candidates & ~same_candidate & unit_in & person_in
    neither_in = valid_candidates & has_bounds & ~unit_in & ~person_in
    insufficient = valid_candidates & ~has_bounds
    veto = one_in & (explicit | conflict)
    # A unique statistical decision changes the rent and basis but remains
    # unverified without source evidence; expose the provenance in the reason.
    review = both_in | neither_in | insufficient | veto | conflict | ~valid_candidates
    out["rent_review_flag"] = review.astype(bool)
    out["rent_review_reason"] = None
    out.loc[both_in, "rent_review_reason"] = "iqr_both_plausible"
    out.loc[neither_in, "rent_review_reason"] = "iqr_neither_plausible"
    out.loc[insufficient, "rent_review_reason"] = "iqr_insufficient_bedroom_reference"
    out.loc[veto, "rent_review_reason"] = "iqr_conflicts_with_source_evidence"
    out.loc[conflict, "rent_review_reason"] = "explicit_quote_amount_conflict"
    out.loc[~valid_candidates, "rent_review_reason"] = "missing_rent_or_bedrooms"

    out["rent_verification_status"] = "plausible_unverified"
    out.loc[explicit & ~conflict, "rent_verification_status"] = "source_verified"
    out.loc[review, "rent_verification_status"] = "review"
    out.loc[supported, "rent_verification_status"] = "iqr_selected_unverified"

    print(
        f"📊 Bedroom-stratified IQR (20 distinct properties minimum): "
        f"{len(bounds)} supported bedroom groups; "
        f"{int(changed.sum())} automatic basis corrections, "
        f"{int(both_in.sum())} both plausible, "
        f"{int(neither_in.sum())} neither plausible, "
        f"{int(insufficient.sum())} insufficient reference, "
        f"{int(review.sum())} review flags"
    )
    return out
