# OpenAI rent-basis classification

The full Cornell Airflow ingest runs deterministic normalization, source-text
OpenAI classification, bedroom-group 1.5× log-IQR selection, and unresolved-
basis review flags inside `extractors.extract_rental_data.extract_rental_data`. It does **not** call external landlord sites.

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


## Four-step rent normalization

1. **Deterministic:** Normalize the advertised `RentAmount` using Cornell's
   `RentType` as an *unverified fallback*. Preserve `rent_per_person_original`.
2. **LLM from details:** OpenAI classifies ONLY what the displayed dollar amount
   represents using the source listing text. It **does not receive** IQR values,
   Cornell's `RentType`, market estimates, or the normalized baseline.
   Distinguish advertised per-bed **pricing** from whole-unit **lease structure**.
   A source-verified, numerically consistent explicit quote can override fallback.
3. **Bedroom-specific log-IQR:** For studio/1BR, 2BR, 3BR, 4BR, and 5+BR,
   take the median rent per property so large buildings don't dominate.
   Require at least **20 distinct properties** in each group. Compute traditional
   lower and upper Tukey fences in log-rent space:
   `exp(Q1 - 1.5 * (Q3-Q1))`, `exp(Q3 + 1.5 * (Q3-Q1))`.
   Compare *both* potential prices, `RentAmount / num_people` and `RentAmount`.
   If exactly one is in the interval, use that interpretation and update
   `rent_per_person` and `rent_final_basis` — **unless verified original
   source evidence or a contradictory dollar quote vetoes the change**.
   A statistical choice is marked `iqr_selected_unverified`, **not verified**.
   For both plausible, neither plausible, or too few reference properties:
   preserve the existing price and flag for review (where applicable).
   Numerically identical interpretations (1BR) cannot be resolved by IQR.
4. **Flag unknown:** Unresolved bases are stored in `rent_final_basis='unknown'`
   with `rent_review_flag` / `rent_review_reason`; the raw `rent_basis`
   remains the separate original OpenAI response for auditing and cache reuse.

The existing `rent_quote_amount_conflict` protects against treating, e.g.,
a quoted `$925/bedroom` as meaning that a displayed `$1,850` amount is also
per-person. An actual quote inconsistent with the advertised amount blocks
automatic LLM/IQR overrides.

New persisted fields: `rent_final_basis`, `rent_iqr_lower_cutoff`,
`rent_iqr_upper_cutoff`, `rent_iqr_reference_provisional`,
`rent_iqr_low_outlier`, `rent_review_flag`, `rent_review_reason`,
`rent_verification_status`.

The curated Supabase view `housing_listings_clean` groups all pricing, AI
source-evidence, and IQR fields immediately before amenities. The base table's
physical PostgreSQL column order remains unchanged.

**Caching:** The change to the text-only v5 prompt invalidates earlier model
cache entries once. Subsequent unchanged source listing descriptions can reuse
cached OpenAI results: statistical final-basis decisions do not overwrite the
raw `rent_basis` fields that are used by the cache. Changing a bedroom-group
reference distribution updates IQR decisions on every full ingest without
forcing an OpenAI reclassification.

**Caveat:** IQR decisions rely on a possibly contaminated baseline, even
though the median and IQR are robust to minority outliers. Source-verified
prices therefore override contradictory IQR decisions. Unverified but
statistically plausible observations are still in the current ML training
path; the flags are not automatically training exclusions.

## Validation

Run `python -m unittest discover -s airflow/tests -p 'test_openai_rent_basis*.py'` and\n`python -m unittest discover -s airflow/tests -p 'test_rent_iqr_audit.py'`
from the repo root with the Airflow dependencies installed. Tests mock the
classifier; they do not spend API credits.

Monitor `🤖 Rent-basis source-evidenced overrides` in pipeline logs and audit
the first sample of accepted changes against landlord pages before depending
on the new training labels.
