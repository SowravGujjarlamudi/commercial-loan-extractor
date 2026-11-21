# Implementation Notes

## Scope

This change adds a CSV loader and row-level validation report for the supplied 20-agreement answer key. The existing Pydantic v2 loan-term schema remains the validation boundary.

## Engineering choices

1. **Pydantic v2** is retained for typed parsing, field constraints, discriminated unions, and cross-field validation.
2. **`Decimal`** is used for commitment amounts and covenant ratios to avoid binary floating-point rounding in financial values.
3. **Optional covenants** remain `Decimal | None`; blank source cells become `None`, never zero. The supplied file has two agreements with both covenant cells blank: `AGR-2026-009` and `AGR-2026-017`.
4. **Discriminated margin union** uses `margin_type` to distinguish flat margins from pricing grids. The model rejects mixed structures and retains every grid tier.
5. **Pricing-grid integrity** requires at least two tiers and strictly increasing leverage thresholds.
6. **CSV-to-model mapping** explicitly maps `borrower_name` to `borrower`, `max_leverage_ratio` to `maximum_leverage_ratio`, and `min_interest_coverage_ratio` to `minimum_interest_coverage_ratio`. The loader parses the JSON-encoded `pricing_grid` cell and retains agreement/reviewer metadata.
7. **Row-level error handling** records a status and validation errors for each source row. Invalid rows are not silently dropped; duplicate agreement IDs cause the affected rows to fail.

## Source-data findings

- Source rows: 20; all 20 passed Pydantic validation (0 failed).
- Unique agreement IDs: 20.
- Flat-margin records: 6.
- Pricing-grid records: 14.
- Missing maximum leverage covenant: 2.
- Missing minimum interest coverage covenant: 2.
- The two records missing both covenants are `AGR-2026-009` and `AGR-2026-017`.
- The CSV does **not** contain an `effective_date` column. The core extraction schema continues to require `effective_date`; a narrow answer-key adapter subtype permits `effective_date=None` for this source and enforces `maturity_date > effective_date` whenever an effective date is supplied. The maturity/effective-date rule cannot be evaluated for these 20 rows from this source alone. No dates have been inferred or fabricated.

## Data handling

The supplied answer-key CSV is treated as local input and is excluded from Git because it contains borrower names and loan terms. Place it at `data/answer_key.csv` (or set `LOAN_ANSWER_KEY_CSV`) when running the dataset-level test. The validation JSON report contains agreement IDs and validation outcomes, not borrower names or commitment amounts.

## Known limitations

- The current answer key does not provide effective dates, so the date relationship check remains pending for this dataset.
- The answer key is an evaluation input, not an extraction source. It is not copied into the repository.
