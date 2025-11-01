"""Validate exchange payloads against simple schema expectations."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Iterable

SCHEMA_SIGNAL_ACK = "signal-ack@1.0"
SCHEMA_FIELD_REPORT = "field-report@1.0"


class ValidationError(Exception):
    """Raised when a payload fails validation."""


def _read_payload(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid JSON: {exc}") from exc


def _require_keys(payload: dict, required: set[str]) -> None:
    missing = required.difference(payload)
    if missing:
        raise ValidationError(f"Missing keys: {sorted(missing)}")


def _validate_timestamp(value: str, field_name: str) -> None:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"{field_name} is not a valid ISO-8601 timestamp") from exc


def _validate_signal_ack(payload: dict) -> None:
    required = {
        "ack_id",
        "referenced_id",
        "sender",
        "receiver",
        "timestamp_sent",
        "status",
    }
    _require_keys(payload, required)
    _validate_timestamp(payload["timestamp_sent"], "timestamp_sent")


def _validate_field_report(payload: dict) -> None:
    required = {
        "report_id",
        "origin",
        "relates_to",
        "timestamp_submitted",
        "status",
        "summary",
    }
    _require_keys(payload, required)
    _validate_timestamp(payload["timestamp_submitted"], "timestamp_submitted")


def _validate_payload(payload: dict) -> None:
    schema = payload.get("schema")
    if not schema:
        raise ValidationError("Missing schema identifier")

    if schema == SCHEMA_SIGNAL_ACK:
        _validate_signal_ack(payload)
        return

    if schema == SCHEMA_FIELD_REPORT:
        _validate_field_report(payload)
        return

    raise ValidationError(f"Unsupported schema '{schema}'")


def _iter_paths(targets: Iterable[str]) -> Iterable[Path]:
    for raw in targets:
        path = Path(raw)
        if path.is_dir():
            for candidate in path.glob("*.json"):
                yield candidate
        else:
            yield path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate exchange payload JSON files.")
    parser.add_argument("paths", nargs="+", help="JSON files or directories to validate")
    args = parser.parse_args(argv)

    exit_code = 0
    for path in _iter_paths(args.paths):
        try:
            payload = _read_payload(path)
            _validate_payload(payload)
        except ValidationError as exc:
            exit_code = 1
            print(f"INVALID: {path} -> {exc}")
        except FileNotFoundError:
            exit_code = 1
            print(f"MISSING: {path}")
        else:
            print(f"VALID: {path}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
