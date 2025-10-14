"""Ingest Toyfoundry samples and update report stub.

Usage:
  python -m tools.consumer_ingest \
    --json .imports/toyfoundry/telemetry/quilt/exports/samples/composite_export.sample.json \
    --csv  .imports/toyfoundry/telemetry/quilt/exports/samples/composite_export.sample.csv \
    --schema .imports/toyfoundry/telemetry/export_schema.md \
    --report exchange/reports/inbox/order-2025-10-14-011-report.json
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Set


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json_records(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # Accept either list[dict] or dict with top-level records key.
    if isinstance(data, list):
        return data  # type: ignore[return-value]
    if isinstance(data, dict):
        for key in ("records", "items", "data"):
            if key in data and isinstance(data[key], list):
                return data[key]
    raise ValueError("Unsupported JSON structure (expected array of objects)")


def load_csv_records(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)  # type: ignore[return-value]


def field_union(records: Iterable[dict[str, Any]]) -> Set[str]:
    fields: Set[str] = set()
    for row in records:
        fields.update(row.keys())
    return fields


def read_schema_version(md_path: Path) -> str | None:
    if not md_path.exists():
        return None
    text = md_path.read_text(encoding="utf-8", errors="ignore")
    # Look for a line like: Schema Version: v1.0
    for line in text.splitlines():
        if "version" in line.lower():
            # naive capture of first token like v1.0
            tokens = [t.strip() for t in line.replace(":", " ").split()]
            for t in tokens:
                if t.lower().startswith("v") and any(ch.isdigit() for ch in t):
                    return t
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Ingest samples and update report JSON")
    ap.add_argument("--json", dest="json_path", required=False)
    ap.add_argument("--csv", dest="csv_path", required=False)
    ap.add_argument("--schema", dest="schema_path", required=False)
    ap.add_argument("--report", dest="report_path", required=True)
    args = ap.parse_args(argv)

    report_file = Path(args.report_path)
    report = json.loads(report_file.read_text(encoding="utf-8"))

    ingestion_notes: list[str] = []
    parse_errors: list[str] = []

    # JSON ingestion
    if args.json_path:
        jpath = Path(args.json_path)
        try:
            jrecs = load_json_records(jpath)
            jfields = sorted(field_union(jrecs))
            report.setdefault("ingestion_log", {})["json"] = {
                "path": str(jpath),
                "records": len(jrecs),
                "fields": jfields,
                "sha256": sha256_of(jpath),
            }
        except Exception as exc:  # noqa: BLE001
            parse_errors.append(f"JSON: {exc}")

    # CSV ingestion
    if args.csv_path:
        cpath = Path(args.csv_path)
        try:
            crecs = load_csv_records(cpath)
            cfields = sorted(field_union(crecs))
            report.setdefault("ingestion_log", {})["csv"] = {
                "path": str(cpath),
                "records": len(crecs),
                "fields": cfields,
                "sha256": sha256_of(cpath),
            }
        except Exception as exc:  # noqa: BLE001
            parse_errors.append(f"CSV: {exc}")

    # Aggregate counts if both present
    total = 0
    for key in ("json", "csv"):
        part = report.get("ingestion_log", {}).get(key)
        if isinstance(part, dict) and isinstance(part.get("records"), int):
            total += part["records"]
    report.setdefault("ingestion_log", {})["records_total"] = total if total else None

    # Schema version
    confirmed_version = None
    if args.schema_path:
        spath = Path(args.schema_path)
        try:
            confirmed_version = read_schema_version(spath)
        except Exception:  # noqa: BLE001
            pass
    report.setdefault("schema_validation", {})["confirmed_version"] = confirmed_version

    # Set acceptance status heuristically
    report.setdefault("acceptance", {})
    if parse_errors:
        report["acceptance"]["status"] = "blocked"
        report["acceptance"]["blockers"] = parse_errors
    else:
        report["acceptance"].setdefault("status", "pending")

    # Notes
    report.setdefault("ingestion_log", {})["notes"] = ingestion_notes

    # Write back
    report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Updated report: {report_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

