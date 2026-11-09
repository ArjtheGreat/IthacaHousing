# Rent basis: persisted review + IQR only

The current Airflow pipeline **does not call an LLM**. Rent-basis decisions
come from the independent, manually/source-verified
`public.rent_basis_reviews` table, followed by bedroom-specific 1.5×
log-space IQR hypothesis testing.

## Why a separate review table?

`public.housing_listings` is truncated on every refresh. Edits only to that
table would be lost. The review table is NOT truncated and stores:

- `listingid` and the exact `source_rentamount` / `source_bedrooms` originally reviewed
- `confirmed_basis`: `per_person`, `per_unit`, or NULL
- `review_status`: `confirmed`, `unverified`, `needs_review`
- Evidence, optional source URL, reviewer and review date

A confirmed decision is applied only if **listing ID, original advertised
price, and original bedroom count all still match**. Changes to price or
bedroom count invalidate reuse until re-reviewed.

## Processing order

1. Deterministic normalization preserves the scraped original price.
2. Confirmed review-table records override `rent_per_person`,
   `total_rent_amount`, `rent_final_basis`, and verification metadata.
   Records marked `needs_review` for building-wide bedroom ambiguity have
   rent/person set to NULL: dividing by a building's combined bedroom count is
   not a legitimate unit normalization.
3. Calculate one median reference rent per property within 1BR, 2BR, 3BR,
   4BR, and 5+BR buckets. **Only independently reviewed rents** are reference
   observations for 2BR and above. 1BR is numerically unambiguous because
   both advertised-price hypotheses yield the same rent/person.
4. For each bucket with at least 8 distinct reference properties, compute
   `Q1` and `Q3` on `log(rent_per_person)`. The accepted interval is:
   `exp(Q1 - 1.5*(Q3-Q1))` through `exp(Q3 + 1.5*(Q3-Q1))`.
5. Compare advertised price and advertised price divided by bedrooms.
   Exactly one in-range -> select that basis and label
   `iqr_selected_unverified`. Both in-range, neither in-range, or insufficient
   verified examples -> preserve the original amount and flag `unknown`.
   Source-reviewed rows **always** retain their confirmed basis.

The 8-independent-property requirement is a conservative operational guard,
not a theorem. No automatic IQR conversion occurs in a bedroom group lacking
an adequate clean reference sample. This is deliberate: the previous
5+BR benchmark included prices near $70/person and was self-contaminated.

## Scope limitation

The November 2026 initial review established 59 source-supported decisions
across 1,036 listings, flagged 8 likely building-wide bedroom-count errors,
and left 969 unverified. A source price may still be ambiguous even when
the rent amount looks plausible. **Do not treat all unverified rows as clean
training targets.**

`rent_basis_openai.py` is retained only for historical reference/testing; it
is no longer imported or called by the Airflow rent normalization step.

Review status and a correction source URL can be inspected directly in the
review table. The main listing table stores the final price, classification,
statistical bounds, and review flags.
