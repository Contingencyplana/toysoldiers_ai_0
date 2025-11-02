"""Factory-order@1.0 ingestion + lore alignment monitor.

Scans telemetry/emoji_runtime/promoted_samples for factory-order payloads,
validates schema + data quality using emoji_translator helpers, and emits a
summary report suitable for after-action notes.

Usage:
  python -m tools.factory_order_monitor \
    --samples telemetry/emoji_runtime/promoted_samples \
    --log logs/factory_order_monitor.log
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Tuple

from tools.emoji_translator import (
    FACTORY_ORDER_SCHEMA,
    load_lexicon,
    validate_factory_order,
)


def iter_payload_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    for path in sorted(root.rglob("*.json")):
        if path.is_file():
            yield path


def load_payload(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # noqa: BLE001
        raise ValueError(f"{path.name}: Invalid JSON ({exc})") from exc


def validate_payload(path: Path, payload: dict) -> Tuple[List[str], List[str]]:
    errors_schema: List[str] = []
    errors_dq: List[str] = []

    schema = payload.get("schema")
    if schema != FACTORY_ORDER_SCHEMA:
        errors_schema.append(f"Expected schema '{FACTORY_ORDER_SCHEMA}', got '{schema}'")

    lexicon = load_lexicon()
    result = validate_factory_order(payload, lexicon)
    errors_schema.extend(result["schema_errors"])
    errors_dq.extend(result["dq_errors"])

    narration = payload.get("narration")
    if narration is not None and not isinstance(narration, dict):
        errors_schema.append("narration must be an object when provided")
    elif isinstance(narration, dict):
        summary = payload.get("summary")
        line = narration.get("line")
        if line is not None and not isinstance(line, str):
            errors_schema.append("narration.line must be a string when provided")
        if (
            isinstance(summary, str)
            and isinstance(line, str)
            and summary.strip()
            and line.strip()
            and summary.strip() != line.strip()
        ):
            errors_dq.append(
                "Summary and narration.line mismatch even after normalization"
            )

    return errors_schema, errors_dq


def write_log(log_path: Path, lines: Iterable[str]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        for line in lines:
            handle.write(line + "\n")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Factory-order monitor for promoted samples")
    parser.add_argument("--samples", default="telemetry/emoji_runtime/promoted_samples", help="Directory containing factory-order payloads")
    parser.add_argument("--log", default="logs/factory_order_monitor.log", help="Path to append monitoring log entries")
    args = parser.parse_args(argv)

    sample_root = Path(args.samples).resolve()
    log_path = Path(args.log).resolve()

    payloads = list(iter_payload_files(sample_root))
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    log_lines: List[str] = [
        f"[{timestamp}] Monitoring run for {sample_root} — {len(payloads)} payload(s)"
    ]

    failures = 0
    for payload_path in payloads:
        try:
            payload = load_payload(payload_path)
        except ValueError as exc:
            log_lines.append(f"  [ERROR] {exc}")
            failures += 1
            continue

        schema_errors, dq_errors = validate_payload(payload_path, payload)
        if schema_errors or dq_errors:
            failures += 1
            log_lines.append(f"  [FAIL] {payload_path.name}")
            for err in schema_errors:
                log_lines.append(f"    schema: {err}")
            for err in dq_errors:
                log_lines.append(f"    dq: {err}")
        else:
            log_lines.append(f"  [OK] {payload_path.name} ({payload.get('summary')})")

    status = "OK" if failures == 0 else "FAIL"
    log_lines.append(f"[{timestamp}] Monitoring complete — status={status}, failures={failures}")
    write_log(log_path, log_lines)

    print("\n".join(log_lines))
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
