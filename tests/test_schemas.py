from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from loan_extractor.schemas import LoanTerms


def base_loan(margin):
    return {
        "borrower": "Example Borrower LLC",
        "commitment_amount": "12500000.00",
        "effective_date": date(2026, 1, 1),
        "maturity_date": date(2031, 1, 1),
        "maximum_leverage_ratio": "4.50",
        "minimum_interest_coverage_ratio": "2.00",
        "margin": margin,
    }


def test_accepts_flat_margin_and_no_grid():
    loan = LoanTerms.model_validate(base_loan({
        "margin_type": "flat",
        "flat_margin_bps": 225,
        "pricing_grid": None,
    }))
    assert loan.margin.margin_type == "flat"


def test_accepts_multi_tier_grid_and_no_flat_rate():
    loan = LoanTerms.model_validate(base_loan({
        "margin_type": "grid",
        "flat_margin_bps": None,
        "pricing_grid": [
            {"leverage_threshold": "1.50", "margin_bps": 125},
            {"leverage_threshold": "2.50", "margin_bps": 150},
            {"leverage_threshold": "3.50", "margin_bps": 175},
        ],
    }))
    assert loan.margin.margin_type == "grid"
    assert len(loan.margin.pricing_grid) == 3


def test_rejects_grid_with_only_one_tier():
    with pytest.raises(ValidationError):
        LoanTerms.model_validate(base_loan({
            "margin_type": "grid",
            "flat_margin_bps": None,
            "pricing_grid": [
                {"leverage_threshold": "1.50", "margin_bps": 125},
            ],
        }))


def test_rejects_grid_with_flat_rate_populated():
    with pytest.raises(ValidationError):
        LoanTerms.model_validate(base_loan({
            "margin_type": "grid",
            "flat_margin_bps": 225,
            "pricing_grid": [
                {"leverage_threshold": "1.50", "margin_bps": 125},
                {"leverage_threshold": "2.50", "margin_bps": 150},
            ],
        }))


def test_rejects_non_increasing_thresholds():
    with pytest.raises(ValidationError):
        LoanTerms.model_validate(base_loan({
            "margin_type": "grid",
            "flat_margin_bps": None,
            "pricing_grid": [
                {"leverage_threshold": "2.50", "margin_bps": 150},
                {"leverage_threshold": "1.50", "margin_bps": 125},
            ],
        }))


def test_allows_missing_covenants():
    data = base_loan({
        "margin_type": "flat",
        "flat_margin_bps": 225,
        "pricing_grid": None,
    })
    data["maximum_leverage_ratio"] = None
    data["minimum_interest_coverage_ratio"] = None
    loan = LoanTerms.model_validate(data)
    assert loan.maximum_leverage_ratio is None
    assert loan.minimum_interest_coverage_ratio is None


def test_rejects_maturity_before_effective_date():
    data = base_loan({
        "margin_type": "flat",
        "flat_margin_bps": 225,
        "pricing_grid": None,
    })
    data["maturity_date"] = date(2025, 12, 31)
    with pytest.raises(ValidationError):
        LoanTerms.model_validate(data)
