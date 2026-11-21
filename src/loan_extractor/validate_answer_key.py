"""Command-line validation report for the labelled answer-key CSV."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from loan_extractor.answer_key import build_validation_report, load_answer_key


def main() -> int:
    parser = argparse.ArgumentParser(description="Load and validate all rows in a loan answer-key CSV.")
    parser.add_argument("--input", required=True, help="Path to the labelled answer-key CSV")
    parser.add_argument("--expected-records", type=int, default=20)
    parser.add_argument("--report-out", default="reports/answer_key_validation.json")
    args = parser.parse_args()

    try:
        result = load_answer_key(args.input)
    except (FileNotFoundError, ValueError) as exc:
        parser.error(str(exc))

    report = build_validation_report(result, expected_records=args.expected_records)

    print("ANSWER KEY VALIDATION — ROW-LEVEL RESULTS")
    print("=" * 78)
    for row in report["rows"]:
        detail = f"{row['margin_type']}"
        if row["margin_type"] == "grid":
            detail += f", {row['pricing_tier_count']} tiers"
        if row["missing_covenants"]:
            detail += ", missing: " + "/".join(row["missing_covenants"])
        print(f"{row['status']:<6} | {row['agreement_id']:<16} | {detail}")
        for error in row["errors"]:
            print(f"       ERROR: {error}")

    print("=" * 78)
    print(f"Rows found:       {report['total_records_found']} (expected {report['expected_records']})")
    print(f"Valid records:    {report['records_validated']}")
    print(f"Failed records:   {report['records_failed']}")
    print(f"Flat margins:     {report['flat_margin_records']}")
    print(f"Pricing grids:    {report['pricing_grid_records']}")
    print(f"Missing max leverage covenant: {report['missing_max_leverage_ratio']}")
    print(f"Missing min coverage covenant: {report['missing_min_interest_coverage_ratio']}")
    print(f"Duplicate IDs:    {len(report['duplicate_agreement_ids'])}")
    if report["date_rule_limitation"]:
        print(f"DATE RULE NOTE:   {report['date_rule_limitation']}")

    report_path = Path(args.report_out)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    markdown_path = report_path.with_suffix(".md")
    markdown_lines = [
        "# Answer-Key Validation Report",
        "",
        f"- Source: `{report['source_file']}`",
        f"- Expected rows: {report['expected_records']}",
        f"- Rows found: {report['total_records_found']}",
        f"- Validated: {report['records_validated']}",
        f"- Failed: {report['records_failed']}",
        f"- Flat margins: {report['flat_margin_records']}",
        f"- Pricing grids: {report['pricing_grid_records']}",
        f"- Missing maximum leverage covenant: {report['missing_max_leverage_ratio']}",
        f"- Missing minimum interest coverage covenant: {report['missing_min_interest_coverage_ratio']}",
        f"- Duplicate agreement IDs: {len(report['duplicate_agreement_ids'])}",
        "",
        "## Row-level results",
        "",
        "| Agreement ID | Status | Margin | Grid tiers | Missing covenants | Errors |",
        "|---|---|---|---:|---|---|",
    ]
    for row in report["rows"]:
        missing = ", ".join(row["missing_covenants"]) or "—"
        errors = "; ".join(row["errors"]) or "—"
        markdown_lines.append(
            f"| {row['agreement_id']} | {row['status']} | {row['margin_type']} | "
            f"{row['pricing_tier_count']} | {missing} | {errors} |"
        )
    if report["date_rule_limitation"]:
        markdown_lines.extend(["", "> **Source limitation:** " + report["date_rule_limitation"]])
    markdown_path.write_text("\n".join(markdown_lines) + "\n", encoding="utf-8")
    print(f"\nDetailed JSON report written to: {report_path}")
    print(f"Markdown report written to: {markdown_path}")

    success = (
        report["record_count_matches_expected"]
        and report["all_records_valid"]
        and not report["duplicate_agreement_ids"]
    )
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
