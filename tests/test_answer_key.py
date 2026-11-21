import csv
import json
import os
from pathlib import Path

import pytest

from loan_extractor.answer_key import build_validation_report, load_answer_key


def write_csv(path: Path, rows: list[dict[str, str]]) -> Path:
    columns = [
        "agreement_id", "borrower_name", "commitment_amount", "maturity_date",
        "margin_type", "flat_margin_bps", "pricing_grid", "max_leverage_ratio",
        "min_interest_coverage_ratio", "checked_by", "checked_date",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    return path


def base_row(agreement_id="AGR-TEST-001"):
    return {
        "agreement_id": agreement_id,
        "borrower_name": "Example Borrower LLC",
        "commitment_amount": "12500000.00",
        "maturity_date": "2031-01-01",
        "margin_type": "flat",
        "flat_margin_bps": "225",
        "pricing_grid": "",
        "max_leverage_ratio": "4.50",
        "min_interest_coverage_ratio": "2.00",
        "checked_by": "Test Reviewer",
        "checked_date": "2026-11-01",
    }


def test_loads_flat_and_grid_rows_and_preserves_optional_covenants(tmp_path):
    flat = base_row("AGR-TEST-001")
    grid = base_row("AGR-TEST-002")
    grid.update({
        "margin_type": "grid",
        "flat_margin_bps": "",
        "pricing_grid": json.dumps([
            {"leverage_threshold": "1.50", "margin_bps": 125},
            {"leverage_threshold": "2.50", "margin_bps": 150},
        ]),
        "max_leverage_ratio": "",
    })
    path = write_csv(tmp_path / "answer_key.csv", [flat, grid])

    result = load_answer_key(path)

    assert result.total_rows == 2
    assert result.valid_count == 2
    assert result.failed_count == 0
    assert result.records[1].terms.maximum_leverage_ratio is None
    assert result.records[1].terms.margin.margin_type == "grid"
    assert len(result.records[1].terms.margin.pricing_grid) == 2


def test_reports_duplicate_agreement_ids_as_failed_rows(tmp_path):
    row1 = base_row("AGR-DUP-001")
    row2 = base_row("AGR-DUP-001")
    path = write_csv(tmp_path / "answer_key.csv", [row1, row2])

    result = load_answer_key(path)

    assert result.duplicate_ids == ["AGR-DUP-001"]
    assert result.failed_count == 2
    assert all(not row.valid for row in result.rows)


def test_rejects_malformed_pricing_grid_json(tmp_path):
    row = base_row()
    row.update({"margin_type": "grid", "flat_margin_bps": "", "pricing_grid": "not-json"})
    path = write_csv(tmp_path / "answer_key.csv", [row])

    result = load_answer_key(path)

    assert result.failed_count == 1
    assert "not valid JSON" in result.rows[0].errors[0]


def test_builds_summary_with_expected_record_count(tmp_path):
    path = write_csv(tmp_path / "answer_key.csv", [base_row()])
    report = build_validation_report(load_answer_key(path), expected_records=20)
    assert report["record_count_matches_expected"] is False
    assert report["total_records_found"] == 1


SOURCE_CSV = Path(os.environ.get("LOAN_ANSWER_KEY_CSV", "data/answer_key.csv"))


@pytest.mark.skipif(not SOURCE_CSV.is_file(), reason="Place the supplied answer key at data/answer_key.csv or set LOAN_ANSWER_KEY_CSV")
def test_all_20_supplied_answer_key_rows_validate():
    result = load_answer_key(SOURCE_CSV)
    report = build_validation_report(result, expected_records=20)

    assert report["total_records_found"] == 20
    assert report["records_validated"] == 20
    assert report["records_failed"] == 0
    assert report["flat_margin_records"] == 6
    assert report["pricing_grid_records"] == 14
    assert report["missing_max_leverage_ratio"] == 2
    assert report["missing_min_interest_coverage_ratio"] == 2
    assert report["duplicate_agreement_ids"] == []
    assert report["effective_date_column_present"] is False
    assert result.records[0].terms.effective_date is None
