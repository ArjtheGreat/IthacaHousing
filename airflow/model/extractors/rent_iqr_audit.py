"""Post-normalization rent anomaly audit.

The LLM determines what the advertised amount covers. This independent
lower-tail log-IQR audit only *flags* suspect values; it NEVER edits rents.
Retains the original 1.2*log-IQR threshold used by Ithaca Insights.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

LOG_IQR_MULTIPLIER = 1.2
MIN_REFERENCE_COUNT = 20


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


def audit_normalized_rents(frame: pd.DataFrame) -> pd.DataFrame:
    """Audit after AI corrections, without overriding evidence-backed rents.

    The reference distribution prioritizes explicitly verified examples so
    misnormalized fallback rows do not determine their own cutoff. When fewer
    than MIN_REFERENCE_COUNT verified examples exist, use all valid rents as
    the reference and mark the bound as provisional.

    A low IQR rent is 'review' unless the LLM supplied an independently
    validated, numerically consistent direct source quote. The flag remains
    visible even for verified anomalies.
    """
    out = frame.copy()
    rents = pd.to_numeric(out["rent_per_person"], errors="coerce")
    valid = rents.notna() & np.isfinite(rents) & rents.gt(0)
    verified = (
        out["rent_basis_evidence_type"].eq("explicit")
        & out["rent_basis_confidence"].eq("high")
        & out["rent_basis"].isin(["per_person", "per_unit"])
    )

    ref = np.log(rents.loc[valid & verified])
    provisional = len(ref) < MIN_REFERENCE_COUNT
    if provisional:
        ref = np.log(rents.loc[valid])
    if len(ref) >= 4:
        p25, p75 = ref.quantile([0.25, 0.75])
        cutoff = float(np.exp(ref.median() - LOG_IQR_MULTIPLIER * (p75 - p25)))
    else:
        cutoff = np.nan

    low = valid & rents.lt(cutoff) if np.isfinite(cutoff) else pd.Series(False, index=out.index)
    contradiction = out.get("rent_quote_amount_conflict", pd.Series(False, index=out.index))
    contradiction = contradiction.fillna(False).astype(bool)
    out["rent_iqr_lower_cutoff"] = cutoff if np.isfinite(cutoff) else np.nan
    out["rent_iqr_reference_provisional"] = bool(provisional)
    out["rent_iqr_low_outlier"] = low.astype(bool)
    out["rent_review_flag"] = (low | contradiction).astype(bool)
    out["rent_review_reason"] = None

    out.loc[low, "rent_review_reason"] = "lower_log_iqr_1_2"
    out.loc[contradiction, "rent_review_reason"] = "explicit_quote_amount_conflict"
    out.loc[low & contradiction, "rent_review_reason"] = (
        "lower_log_iqr_1_2;explicit_quote_amount_conflict"
    )

    out["rent_verification_status"] = "plausible_unverified"
    out.loc[verified & ~contradiction, "rent_verification_status"] = "source_verified"
    out.loc[~valid, "rent_verification_status"] = "review"
    out.loc[(low & ~verified) | contradiction, "rent_verification_status"] = "review"

    print(
        "📊 Post-LLM rent audit: "
        f"cutoff=${cutoff:,.0f} ({'provisional' if provisional else 'verified reference'}), "
        f"{int(low.sum())} low outliers, {int(contradiction.sum())} quote conflicts, "
        f"{int(out['rent_review_flag'].sum())} flagged for review; "
        "no IQR rent corrections"
    )
    return out
