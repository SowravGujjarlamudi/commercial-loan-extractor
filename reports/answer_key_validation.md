# Answer-Key Validation Report

- Source: `answer_key.csv`
- Expected rows: 20
- Rows found: 20
- Validated: 20
- Failed: 0
- Flat margins: 6
- Pricing grids: 14
- Missing maximum leverage covenant: 2
- Missing minimum interest coverage covenant: 2
- Duplicate agreement IDs: 0

## Row-level results

| Agreement ID | Status | Margin | Grid tiers | Missing covenants | Errors |
|---|---|---|---:|---|---|
| AGR-2026-001 | VALID | grid | 4 | — | — |
| AGR-2026-004 | VALID | flat | 0 | — | — |
| AGR-2026-006 | VALID | grid | 4 | — | — |
| AGR-2026-008 | VALID | grid | 3 | — | — |
| AGR-2026-009 | VALID | flat | 0 | max_leverage_ratio, min_interest_coverage_ratio | — |
| AGR-2026-012 | VALID | grid | 3 | — | — |
| AGR-2026-014 | VALID | grid | 5 | — | — |
| AGR-2026-015 | VALID | flat | 0 | — | — |
| AGR-2026-017 | VALID | grid | 3 | max_leverage_ratio, min_interest_coverage_ratio | — |
| AGR-2026-019 | VALID | grid | 4 | — | — |
| AGR-2026-021 | VALID | grid | 4 | — | — |
| AGR-2026-023 | VALID | flat | 0 | — | — |
| AGR-2026-025 | VALID | grid | 4 | — | — |
| AGR-2026-028 | VALID | flat | 0 | — | — |
| AGR-2026-030 | VALID | grid | 3 | — | — |
| AGR-2026-031 | VALID | grid | 4 | — | — |
| AGR-2026-034 | VALID | grid | 4 | — | — |
| AGR-2026-036 | VALID | flat | 0 | — | — |
| AGR-2026-038 | VALID | grid | 3 | — | — |
| AGR-2026-040 | VALID | grid | 3 | — | — |

> **Source limitation:** The source answer key does not provide effective_date for every record; maturity-after-effective-date cannot be evaluated for those records.
