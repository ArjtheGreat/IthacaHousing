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
is sent with its floorplans, original advertised rents, source pricing
metadata, descriptions, and leasing information (in chunks for large properties).

For each listing the response is:
`rent_basis` (`per_person`, `per_unit`, `unknown`),
`rent_basis_confidence`, `rent_basis_evidence_type`,
`rent_basis_evidence`, `rent_basis_source`, and `rent_basis_fingerprint`.

Only **high-confidence, explicit, quoted source evidence** that corroborates
an AI classification can override the original Cornell `RentType`
normalization. The numeric calculation is deterministic:
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

**Caching:** Before the full ingest replaces the listings table, the classifier reads prior decisions from Supabase. It computes a SHA-256 fingerprint of the full relevant property/chunk source payload, the prompt version, and the configured model. It skips the API whenever every floorplan in the chunk already has a saved `rent_basis_confidence` and a matching fingerprint. `unknown`/low-confidence results are cached too (they stay unverified); failed calls are not cached. If a floorplan, property description, model ID, or prompt changes, that chunk is audited again. A new floorplan in the same chunk may require rechecking existing units to retain property context. The first run will call the API because existing rows lack fingerprints. A full refresh still rewrites the table, but it retains the cached decisions through the in-memory dataframe. The cache is not dependent on prior `rent_per_person` values.

The classifier is only invoked by **full ingest** when classifications are missing or stale.
The database-only rent-model rerun does not scrape source data and does **not**
rerun the classifier; it uses the last saved `rent_per_person` values.
The Airflow DAG ID is `retrain_rental_model` (`airflow/dags/housing_data_training.py`). Its schedule is `0 12 * * *` in Airflow's configured timezone. No change is made to live Supabase until that DAG runs.

## Validation

Run `python -m unittest discover -s airflow/tests -p 'test_openai_rent_basis.py'`
from the repo root with the Airflow dependencies installed. Tests mock the
classifier; they do not spend API credits.

Monitor `🤖 Rent-basis source-evidenced overrides` in pipeline logs and audit
the first sample of accepted changes against landlord pages before depending
on the new training labels.
