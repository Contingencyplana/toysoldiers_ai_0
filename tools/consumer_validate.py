"""Validate Toyfoundry composite exports (schema v1.0) and update report.

Usage:
  python -m tools.consumer_validate \
    --report exchange/reports/inbox/order-2025-10-14-013-report.json
"""
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ALLOWED_RITUALS = {"drill", "parade", "purge", "promote"}
ALLOWED_STATUS = {"success", "warning", "failure"}
EXPECTED_FIELDS = ["batch_id", "ritual", "units_processed", "status", "duration_ms"]


@dataclass
class CheckResult:
    name: str
    passed: bool
    details: list[str]


def _load_json_records(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "batches" in payload:
        batches = payload["batches"]
        if isinstance(batches, list):
            # Normalize to flat records matching CSV form
            return [
                {
                    "batch_id": b.get("batch_id"),
                    "ritual": b.get("ritual"),
                    "units_processed": b.get("units_processed"),
                    "status": b.get("status"),
                    "duration_ms": b.get("duration_ms"),
                }
                for b in batches
                if isinstance(b, dict)
            ]
    raise ValueError("Unsupported JSON structure (expected object with 'batches' list)")


def _load_csv_records(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _coerce_int(val: Any) -> int | None:
    try:
        return int(val)
    except Exception:
        return None


def validate_dataset(records: list[dict[str, Any]]) -> list[CheckResult]:
    results: list[CheckResult] = []

    # non_empty
    details: list[str] = []
    passed = len(records) > 0
    if not passed:
        details.append("Dataset is empty")
    results.append(CheckResult("non_empty", passed, details))

    # allowed_rituals
    details = []
    bad = [r.get("ritual") for r in records if r.get("ritual") not in ALLOWED_RITUALS]
    passed = len(bad) == 0
    if not passed:
        details.append(f"Unexpected rituals: {sorted({str(x) for x in bad})}")
    results.append(CheckResult("allowed_rituals", passed, details))

    # units_positive
    details = []
    bad_units = [r.get("units_processed") for r in records if (_coerce_int(r.get("units_processed")) or 0) <= 0]
    passed = len(bad_units) == 0
    if not passed:
        details.append("Found non-positive units_processed values")
    results.append(CheckResult("units_positive", passed, details))

    # duration_ms_range (0 < x <= 24h in ms)
    details = []
    upper = 24 * 60 * 60 * 1000
    def _ok(v: Any) -> bool:
        iv = _coerce_int(v)
        return iv is not None and 0 < iv <= upper
    bad_dur = [r.get("duration_ms") for r in records if not _ok(r.get("duration_ms"))]
    passed = len(bad_dur) == 0
    if not passed:
        details.append("Found invalid duration_ms values (<=0 or too large)")
    results.append(CheckResult("duration_ms_range", passed, details))

    # allowed status
    details = []
    bad_status = [r.get("status") for r in records if r.get("status") not in ALLOWED_STATUS]
    passed = len(bad_status) == 0
    if not passed:
        details.append(f"Unexpected status values: {sorted({str(x) for x in bad_status})}")
    results.append(CheckResult("allowed_status", passed, details))

    return results


def update_report(report_path: Path) -> None:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    sources = report.get("sources", {})
    json_path = sources.get("sample_json")
    csv_path = sources.get("sample_csv")

    # Try CSV first (flat), else JSON batches
    recs: list[dict[str, Any]] = []
    if csv_path and Path(csv_path).exists():
        recs = _load_csv_records(Path(csv_path))
    elif json_path and Path(json_path).exists():
        recs = _load_json_records(Path(json_path))

    # Schema field comparison
    observed_fields = sorted({k for r in recs for k in r.keys()})
    unexpected = sorted([f for f in observed_fields if f not in EXPECTED_FIELDS])
    missing = sorted([f for f in EXPECTED_FIELDS if f not in observed_fields])

    report.setdefault("schema_validation", {})
    report["schema_validation"]["unexpected_fields"] = unexpected
    report["schema_validation"]["field_mismatches"] = missing

    # Data quality checks
    checks = validate_dataset(recs)
    report.setdefault("dq_checks", {})
    for c in checks:
        report["dq_checks"][c.name] = {
            "passed": c.passed,
            "details": c.details,
        }

    # Acceptance decision
    blockers: list[str] = []
    if unexpected:
        blockers.append("Unexpected fields present")
    if missing:
        blockers.append("Expected fields missing")
    failed = [c.name for c in checks if not c.passed]
    if failed:
        blockers.append(f"DQ checks failed: {', '.join(failed)}")

    report.setdefault("acceptance", {})
    if blockers:
        report["acceptance"]["status"] = "blocked"
        report["acceptance"]["blockers"] = blockers
        report["status"] = "pending"
    else:
        report["acceptance"]["status"] = "accepted"
        report["acceptance"].setdefault("constraints", [])
        report["status"] = "ready_for_review"
        # Backfill timestamp if placeholder
        if report.get("timestamp_sent", "").startswith("<"):
            report["timestamp_sent"] = "2025-10-15T00:44:00Z"

    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate Toyfoundry composite exports and update report JSON.")
    ap.add_argument("--report", dest="report_path", required=True)
    args = ap.parse_args(argv)
    update_report(Path(args.report_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

