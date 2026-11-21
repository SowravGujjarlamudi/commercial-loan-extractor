# Commercial Loan Extractor

A Python starter project for validating structured commercial-loan terms extracted from credit agreements and loan contracts.

## Requirements

- Python 3.11+
- pip

## Setup

### 1. Create and activate a virtual environment

**Windows PowerShell**
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Run tests

```bash
pytest -q
```

## Current validation scope

- Borrower name: required, non-whitespace, maximum 200 characters.
- Commitment amount: positive `Decimal`, maximum 2 decimal places.
- Effective and maturity dates: maturity must follow effective date.
- Maximum leverage and minimum interest coverage covenants: optional; if present, must be positive.
- Margin: discriminated union keyed by `margin_type`.
  - `flat`: `flat_margin_bps` is populated and `pricing_grid` must be `None`.
  - `grid`: `flat_margin_bps` must be `None`; `pricing_grid` must contain at least two tiers.
- Each pricing tier stores `leverage_threshold` and `margin_bps`.
- Grid thresholds must be strictly increasing.
- Unknown fields are rejected.

## Project layout

```text
commercial-loan-extractor/
├── src/
│   └── loan_extractor/
│       ├── __init__.py
│       └── schemas.py
├── tests/
│   └── test_schemas.py
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
└── README.md
```

## GitHub setup

Create an empty repository on GitHub named `commercial-loan-extractor`, then run:

```bash
git init
git add .
git commit -m "Initial loan extraction validation project"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/commercial-loan-extractor.git
git push -u origin main
```

Do not commit real loan agreements, borrower data, API keys, or `.env` files.
