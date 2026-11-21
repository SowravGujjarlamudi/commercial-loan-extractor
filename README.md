# Commercial Loan Extractor

A Python project for validating structured commercial-loan terms extracted from credit agreements and loan contracts, including a loader for a labelled answer-key CSV.

## Requirements

- Python 3.11+
- pip

## Setup

### Windows (Command Prompt)

```cmd
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m pip install -e .
```

### macOS / Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
```

## Validate the answer key

Place the supplied CSV at `data/answer_key.csv`. The source answer key is intentionally excluded from Git because it contains borrower and loan information.

```bash
python -m loan_extractor.validate_answer_key --input "data/answer_key.csv"
```

Optional arguments:

- `--expected-records 20` (default: 20)
- `--report-out reports/answer_key_validation.json` (default shown)

The command prints one result per source row, followed by totals and any source-data limitations. It writes both JSON and Markdown reports (the Markdown report uses the same filename with a `.md` extension). It returns a non-zero exit code if the row count differs from the expected count, any row fails validation, or duplicate agreement IDs are found.

Alternatively, set `LOAN_ANSWER_KEY_CSV` to the CSV path for the dataset-level pytest.

## Run automated tests

```bash
pytest -q
```

The dataset-level test validates all 20 rows when `data/answer_key.csv` is present (or `LOAN_ANSWER_KEY_CSV` is set). Other loader and schema tests use isolated temporary fixtures.

## Validation rules

- Borrower name: required, non-whitespace, maximum 200 characters.
- Commitment amount: positive `Decimal`, maximum two decimal places.
- Effective date: required by the core extraction schema. The answer-key adapter permits it to be absent because this CSV has no `effective_date` column; when supplied, maturity must be later.
- Maturity date: required.
- Maximum leverage and minimum interest coverage covenants: optional; if present, must be positive.
- Margin: discriminated union keyed by `margin_type`.
  - `flat`: `flat_margin_bps` is populated and `pricing_grid` is null.
  - `grid`: `flat_margin_bps` is null; `pricing_grid` has at least two tiers.
- Pricing-grid leverage thresholds must be strictly increasing.
- Unknown fields are rejected.

## Project layout

```text
commercial-loan-extractor/
├── IMPLEMENTATION_NOTES.md
├── README.md
├── src/loan_extractor/
│   ├── __init__.py
│   ├── answer_key.py
│   ├── schemas.py
│   └── validate_answer_key.py
├── tests/
│   ├── test_answer_key.py
│   └── test_schemas.py
├── data/                  # local input; CSV excluded from Git
├── reports/               # generated validation report
├── .env.example
├── .gitignore
├── pyproject.toml
└── requirements.txt
```

## GitHub

The project repository is `https://github.com/SowravGujjarlamudi/commercial-loan-extractor`. Commit and push from your authenticated local Git environment; do not commit the source answer-key CSV, real loan agreements, API keys, or `.env` files.
