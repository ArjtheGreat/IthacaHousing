# OpenAI rent-basis classification

The full Cornell Airflow ingest runs `extractors.rent_basis_openai.classify_rent_bases`
inside `extractors.extract_rental_data.extract_rental_data`, before the
`rent_per_person` training target is used. This replaces the earlier automatic
lower-tail log-IQR conversion. It does **not** call external landlord sites.

## Configuration

- `OPENAI_API_KEY`: API key configured in the **Airflow runtime**, not committed.
- `RENT_BASIS_OPENAI_ENABLED=1`: enabled by default; set to `0` to opt out.
- `RENT_BASIS_OPENAI_MODEL=gpt-4.1-mini`: configurable model ID.

Install `openai` from `airflow/requirements.txt`. The code uses the OpenAI
Chat Completions API with strict JSON-schema structured outputs. Each property
is sent with its floorplans, original advertised rents, floorplan-specific source pricing
metadata, descriptions, and leasing information (in chunks for large properties).
**Cornell's property-level `RentType` is withheld from the model** because the
purpose of the audit is to check whether that label is wrong.

For each listing the response is:
`rent_basis` (`per_person`, `per_unit`, `unknown`),
`rent_basis_confidence`, `rent_basis_evidence_type`,
`rent_basis_evidence`, `rent_basis_evidence_field`, `rent_basis_source`,
and `rent_basis_fingerprint`.

Only **high-confidence, explicit, quoted source evidence** that corroborates
an AI classification can override the original Cornell `RentType`
normalization. OpenAI must return an **exact contiguous quote** and the precise
source field (`unit_name`, `source_description`, `floorplan_rent_style`,
`floorplan_per_person`, or `property_description`). Python validates that
field/quote pairing and checks for rent-basis language such as `per person`,
`by the bed rent price`, `pricing is listed by bed`, or `entire unit rent`.
Property-wide statements describing only 2BR/3BR units cannot verify a 1BR.
Generic leasing availability and `individual leases offered` alone cannot
verify a unit's price basis. The numeric calculation is deterministic:
- `per_person` → `rent_per_person = RentAmount`
- `per_unit` → `rent_per_person = RentAmount / num_people`

`num_people` currently defaults to the available bedroom count, including
studio = 1. This is an approximation and is not adequate for shared rooms.

The source-normalized amount is preserved in
`rent_per_person_original`. Evidence-backed overrides are flagged in
`ithaca_insights_adjustment` with the `pricing_adjustment_reason`. The
classification and supporting evidence are saved as columns in Supabase.

**Unknown/inferred basis, failed API call, or missing key:**
The pipeline retains the existing Cornell `RentType` normalization, without
claiming it is verified. Do not treat `unknown` as an audited label. Log and
review ambiguous units against original landlord pages.

**Caching:** Before the full ingest replaces the listings table, the classifier reads prior decisions from Supabase. It computes a SHA-256 fingerprint of the full relevant property/chunk source payload, the prompt version, and the configured model. It skips the API whenever every floorplan in the chunk already has a saved `rent_basis_confidence` and a matching fingerprint. `unknown`/low-confidence results are cached too (they stay unverified); failed calls are not cached. If a floorplan, property description, model ID, or prompt changes, that chunk is audited again. The v3 prompt and evidence-schema update intentionally invalidates the v2 cache **once**; budget for reclassification of all properties on the first new run. A new floorplan in the same chunk may require rechecking existing units to retain property context. The first run will call the API because existing rows lack fingerprints. A full refresh still rewrites the table, but it retains the cached decisions through the in-memory dataframe. The cache is not dependent on prior `rent_per_person` values.

The classifier is only invoked by **full ingest** when classifications are missing or stale.
The database-only rent-model rerun does not scrape source data and does **not**
rerun the classifier; it uses the last saved `rent_per_person` values.
The Airflow DAG ID is `retrain_rental_model` (`airflow/dags/housing_data_training.py`). Its schedule is `0 12 * * *` in Airflow's configured timezone. No change is made to live Supabase until that DAG runs.


## IQR context before OpenAI

The full-ingest extractor runs `pre_classification_iqr_context` **before**
`classify_rent_bases`. It uses the existing source-normalized per-person
values to calculate the original 1.2× lower log-IQR cutoff. For every
floorplan it sends the OpenAI model BOTH possible interpretations:
`RentAmount / num_people` (per-unit hypothesis) and `RentAmount`
(per-person hypothesis), and whether each falls below that provisional
cutoff. The raw `RentType` is still withheld from the AI.

These IQR diagnostics are deliberately **not** verification. A suspicious
value must not become `explicit` or `high` confidence solely because its
alternative looks statistically plausible. Automatic changes still require
independent literal source evidence. The provisional benchmark may itself be
contaminated by incorrectly normalized listings.

The classifier cache fingerprint includes these diagnostics and the v4
prompt version. **The first run after this change reclassifies existing
properties**; identical later runs reuse their cached results. Changes to
the global cutoff may invalidate more property groups.

## Post-LLM IQR audit

After the model classifies source price bases and Python calculates rents,
`extractors.rent_iqr_audit.audit_normalized_rents` applies the original
**lower-tail log-IQR** rule, `exp(median(log(r)) - 1.2 * IQR(log(r)))`.
The reference distribution favors explicitly verified listings when at least
20 are available; otherwise it uses the full priced sample and records that
cutoff as provisional. This is an **audit only**, not another rent correction.

The following fields are persisted to Supabase:
`rent_iqr_lower_cutoff`, `rent_iqr_reference_provisional`,
`rent_iqr_low_outlier`, `rent_quote_amount_conflict`,
`rent_review_flag`, `rent_review_reason`, `rent_verification_status`.
The status is `source_verified`, `plausible_unverified`, or `review`.
Outliers with strong source evidence can remain `source_verified` while also
having `rent_review_flag=true`; IQR does not overrule the quoted price.

A dollar amount quoted as e.g. `$925 per bedroom` when the original
advertisement is `$1,850` is treated as a numeric inconsistency. It prevents
a naive automatic `per_person` override of the full $1,850 amount and
flags the unit for review. Neither an IQR flag nor LLM confidence alone
can supply a corrected rent. Rows marked `review` are still retained in
the base table and current model-training path; the review status is **not**
yet a training exclusion filter.

The canonical `housing_listings` table retains its physical PostgreSQL
column order (PostgreSQL does not support column moves). For a readable
Supabase column layout use **`housing_listings_clean`**, whose pricing,
classification and IQR audit fields are contiguous immediately before
`amenities` in the refreshed view. Recreating the base table only to
change UI column order is intentionally avoided.

## Validation

Run `python -m unittest discover -s airflow/tests -p 'test_openai_rent_basis*.py'` and\n`python -m unittest discover -s airflow/tests -p 'test_rent_iqr_audit.py'`
from the repo root with the Airflow dependencies installed. Tests mock the
classifier; they do not spend API credits.

Monitor `🤖 Rent-basis source-evidenced overrides` in pipeline logs and audit
the first sample of accepted changes against landlord pages before depending
on the new training labels.
