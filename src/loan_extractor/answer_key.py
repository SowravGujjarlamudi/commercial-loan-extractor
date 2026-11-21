"""Load and validate the labelled commercial-loan answer-key CSV."""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from loan_extractor.schemas import LoanTerms


class AnswerKeyTerms(LoanTerms):
    """Answer-key variant: effective_date is optional when absent in the source CSV."""

    effective_date: date | None = None


REQUIRED_COLUMNS = {
    "agreement_id",
    "borrower_name",
    "commitment_amount",
    "maturity_date",
    "margin_type",
    "flat_margin_bps",
    "pricing_grid",
    "max_leverage_ratio",
    "min_interest_coverage_ratio",
    "checked_by",
    "checked_date",
}
OPTIONAL_COLUMNS = {"effective_date"}


class AnswerKeyRecord(BaseModel):
    """A validated loan term record plus answer-key provenance metadata."""

    model_config = ConfigDict(extra="forbid")

    agreement_id: str = Field(min_length=1)
    checked_by: str = Field(min_length=1)
    checked_date: date
    terms: AnswerKeyTerms


@dataclass
class RowResult:
    row_number: int
    agreement_id: str
    valid: bool
    margin_type: str = "unknown"
    pricing_tier_count: int = 0
    missing_covenants: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class AnswerKeyLoadResult:
    source_path: str
    total_rows: int
    records: list[AnswerKeyRecord]
    rows: list[RowResult]
    duplicate_ids: list[str]
    effective_date_column_present: bool

    @property
    def valid_count(self) -> int:
        return sum(row.valid for row in self.rows)

    @property
    def failed_count(self) -> int:
        return self.total_rows - self.valid_count


def _optional_decimal(value: str | None) -> Decimal | None:
    if value is None or not value.strip():
        return None
    try:
        return Decimal(value.strip())
    except InvalidOperation as exc:
        raise ValueError(f"Invalid decimal value: {value!r}") from exc


def _optional_int(value: str | None) -> int | None:
    if value is None or not value.strip():
        return None
    try:
        parsed = Decimal(value.strip())
    except InvalidOperation as exc:
        raise ValueError(f"Invalid integer value: {value!r}") from exc
    if parsed != parsed.to_integral_value():
        raise ValueError(f"Expected a whole number, received {value!r}")
    return int(parsed)


def _parse_row(raw: dict[str, str], effective_date_column_present: bool) -> AnswerKeyRecord:
    agreement_id = (raw.get("agreement_id") or "").strip()
    borrower = (raw.get("borrower_name") or "").strip()
    margin_type = (raw.get("margin_type") or "").strip().lower()

    if margin_type not in {"flat", "grid"}:
        raise ValueError(f"Unsupported margin_type: {margin_type!r}")

    flat_margin_bps = _optional_int(raw.get("flat_margin_bps"))
    grid_text = raw.get("pricing_grid") or ""
    pricing_grid: Any = None
    if grid_text.strip():
        try:
            pricing_grid = json.loads(grid_text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"pricing_grid is not valid JSON: {exc.msg}") from exc

    margin = {
        "margin_type": margin_type,
        "flat_margin_bps": flat_margin_bps,
        "pricing_grid": pricing_grid,
    }

    effective_date_value = None
    if effective_date_column_present:
        effective_date_text = (raw.get("effective_date") or "").strip()
        effective_date_value = date.fromisoformat(effective_date_text) if effective_date_text else None

    terms_data = {
        "borrower": borrower,
        "commitment_amount": _optional_decimal(raw.get("commitment_amount")),
        "effective_date": effective_date_value,
        "maturity_date": date.fromisoformat((raw.get("maturity_date") or "").strip()),
        "maximum_leverage_ratio": _optional_decimal(raw.get("max_leverage_ratio")),
        "minimum_interest_coverage_ratio": _optional_decimal(raw.get("min_interest_coverage_ratio")),
        "margin": margin,
    }

    return AnswerKeyRecord.model_validate(
        {
            "agreement_id": agreement_id,
            "checked_by": (raw.get("checked_by") or "").strip(),
            "checked_date": date.fromisoformat((raw.get("checked_date") or "").strip()),
            "terms": AnswerKeyTerms.model_validate(terms_data),
        }
    )


def load_answer_key(path: str | Path) -> AnswerKeyLoadResult:
    """Load every CSV row, retaining a row-level result for successes and failures."""
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"Answer-key CSV not found: {source}")

    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = set(reader.fieldnames or [])
        missing_headers = sorted(REQUIRED_COLUMNS - headers)
        if missing_headers:
            raise ValueError(f"CSV is missing required columns: {', '.join(missing_headers)}")
        effective_date_column_present = "effective_date" in headers
        raw_rows = list(reader)

    id_counts = Counter((row.get("agreement_id") or "").strip() for row in raw_rows)
    duplicate_ids = sorted(identifier for identifier, count in id_counts.items() if identifier and count > 1)

    records: list[AnswerKeyRecord] = []
    row_results: list[RowResult] = []

    for row_number, raw in enumerate(raw_rows, start=2):
        agreement_id = (raw.get("agreement_id") or "").strip() or f"<missing-id-row-{row_number}>"
        margin_type = (raw.get("margin_type") or "").strip().lower() or "unknown"
        grid_text = raw.get("pricing_grid") or ""
        tier_count = 0
        if grid_text.strip():
            try:
                parsed_grid = json.loads(grid_text)
                tier_count = len(parsed_grid) if isinstance(parsed_grid, list) else 0
            except json.JSONDecodeError:
                pass

        missing_covenants = []
        if not (raw.get("max_leverage_ratio") or "").strip():
            missing_covenants.append("max_leverage_ratio")
        if not (raw.get("min_interest_coverage_ratio") or "").strip():
            missing_covenants.append("min_interest_coverage_ratio")

        errors: list[str] = []
        if agreement_id in duplicate_ids:
            errors.append("Duplicate agreement_id in source CSV")
        try:
            record = _parse_row(raw, effective_date_column_present)
            if not errors:
                records.append(record)
        except (ValueError, ValidationError, TypeError) as exc:
            if isinstance(exc, ValidationError):
                errors.extend(
                    f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}"
                    for item in exc.errors()
                )
            else:
                errors.append(str(exc))

        row_results.append(
            RowResult(
                row_number=row_number,
                agreement_id=agreement_id,
                valid=not errors,
                margin_type=margin_type,
                pricing_tier_count=tier_count,
                missing_covenants=missing_covenants,
                errors=errors,
            )
        )

    return AnswerKeyLoadResult(
        source_path=str(source),
        total_rows=len(raw_rows),
        records=records,
        rows=row_results,
        duplicate_ids=duplicate_ids,
        effective_date_column_present=effective_date_column_present,
    )


def build_validation_report(result: AnswerKeyLoadResult, expected_records: int = 20) -> dict[str, Any]:
    flat_count = sum(row.valid and row.margin_type == "flat" for row in result.rows)
    grid_count = sum(row.valid and row.margin_type == "grid" for row in result.rows)
    max_lev_missing = sum("max_leverage_ratio" in row.missing_covenants for row in result.rows)
    min_coverage_missing = sum("min_interest_coverage_ratio" in row.missing_covenants for row in result.rows)
    effective_date_count = sum(record.terms.effective_date is not None for record in result.records)

    return {
        "source_file": Path(result.source_path).name,
        "expected_records": expected_records,
        "total_records_found": result.total_rows,
        "records_validated": result.valid_count,
        "records_failed": result.failed_count,
        "record_count_matches_expected": result.total_rows == expected_records,
        "all_records_valid": result.failed_count == 0,
        "flat_margin_records": flat_count,
        "pricing_grid_records": grid_count,
        "missing_max_leverage_ratio": max_lev_missing,
        "missing_min_interest_coverage_ratio": min_coverage_missing,
        "duplicate_agreement_ids": result.duplicate_ids,
        "effective_date_column_present": result.effective_date_column_present,
        "records_with_effective_date": effective_date_count,
        "date_rule_limitation": None if effective_date_count == result.valid_count else (
            "The source answer key does not provide effective_date for every record; "
            "maturity-after-effective-date cannot be evaluated for those records."
        ),
        "rows": [
            {
                "row_number": row.row_number,
                "agreement_id": row.agreement_id,
                "status": "VALID" if row.valid else "FAILED",
                "margin_type": row.margin_type,
                "pricing_tier_count": row.pricing_tier_count,
                "missing_covenants": row.missing_covenants,
                "errors": row.errors,
            }
            for row in result.rows
        ],
    }
