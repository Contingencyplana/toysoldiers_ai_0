"""Order 021 validation with factory-order@1.0 awareness."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, List, Mapping, Sequence, Tuple

from tools.emoji_translator import (
    FACTORY_ORDER_SCHEMA,
    load_lexicon,
    validate_factory_order,
    validate_telemetry_dq,
    validate_telemetry_schema,
)

DEFAULT_IMPORTS_DIR = Path(__file__).parents[1] / ".imports" / "toyfoundry" / "telemetry" / "quilt" / "exports"
SCHEMA_VERSION = "v1.0"


def validate_sha256(file_path: Path, expected_hash: str) -> Tuple[bool, str]:
    """Verify SHA256 checksum."""
    if not file_path.exists():
        return False, f"File not found: {file_path}"

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as handle:
        for chunk in iter(lambda: handle.read(4096), b""):
            sha256_hash.update(chunk)

    actual = sha256_hash.hexdigest()
    if actual != expected_hash:
        return False, f"Hash mismatch: expected {expected_hash}, got {actual}"

    return True, "OK"


def _coerce_payload(content: Any) -> Sequence[Any]:
    if isinstance(content, list):
        return content
    if isinstance(content, Mapping) and isinstance(content.get("batches"), list):
        return content["batches"]
    raise ValueError("Unsupported payload structure (expected list or object with 'batches')")


def _partition_records(records: Sequence[Any]) -> Tuple[List[Tuple[int, Mapping[str, Any]]], List[Tuple[int, Mapping[str, Any]]], List[int]]:
    factory_orders: List[Tuple[int, Mapping[str, Any]]] = []
    telemetry_only: List[Tuple[int, Mapping[str, Any]]] = []
    unsupported: List[int] = []

    for idx, record in enumerate(records):
        if isinstance(record, Mapping) and record.get("schema") == FACTORY_ORDER_SCHEMA:
            factory_orders.append((idx, record))
        elif isinstance(record, Mapping):
            telemetry_only.append((idx, record))
        else:
            unsupported.append(idx)

    return factory_orders, telemetry_only, unsupported


def _validate_legacy_telemetry(entries: List[Tuple[int, Mapping[str, Any]]]) -> Tuple[List[str], List[str]]:
    schema_errors: List[str] = []
    dq_errors: List[str] = []
    for original_idx, record in entries:
        schema_errors.extend(
            f"Record[{original_idx}]: {err}" for err in validate_telemetry_schema([record])
        )
        dq_errors.extend(
            f"Record[{original_idx}]: {err}" for err in validate_telemetry_dq([record])
        )
    return schema_errors, dq_errors


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Toyfoundry composite exports for Order 021.")
    parser.add_argument(
        "--imports",
        dest="imports_dir",
        default=str(DEFAULT_IMPORTS_DIR),
        help="Directory containing composite_export artifacts (default: consumer imports)",
    )
    args = parser.parse_args(argv)

    imports_dir = Path(args.imports_dir)

    print("=" * 60)
    print("ORDER 021: Consumer Validation for Standard Run")
    print("=" * 60)

    # Step 1: Verify SHA256 checksums
    print("\n[Step 1] Verifying SHA256 checksums...")
    manifest_path = imports_dir / "export_manifest.json"

    if not manifest_path.exists():
        print(f"❌ export_manifest.json not found at {manifest_path}")
        return 1

    with open(manifest_path, encoding="utf-8") as handle:
        manifest = json.load(handle)

    checksum_errors: List[str] = []
    artifacts = manifest.get("artifacts", [])

    if artifacts:
        for artifact in artifacts:
            file_path = imports_dir / artifact["filename"]
            expected_hash = artifact.get("sha256", "")
            if not expected_hash:
                checksum_errors.append(f"No checksum for {artifact['filename']}")
                continue
            valid, msg = validate_sha256(file_path, expected_hash)
            if valid:
                print(f"  ✓ {artifact['filename']}: {msg}")
            else:
                print(f"  ✗ {artifact['filename']}: {msg}")
                checksum_errors.append(msg)
    else:
        for filename, expected_hash in manifest.get("checksums", {}).items():
            file_path = imports_dir / filename
            valid, msg = validate_sha256(file_path, expected_hash)
            if valid:
                print(f"  ✓ {filename}: {msg}")
            else:
                print(f"  ✗ {filename}: {msg}")
                checksum_errors.append(msg)

    # Step 2: Validate schema
    print(f"\n[Step 2] Validating schema {SCHEMA_VERSION} and factory orders...")
    composite_json = imports_dir / "composite_export.json"

    if not composite_json.exists():
        print("❌ composite_export.json not found")
        return 1

    with open(composite_json, encoding="utf-8") as handle:
        payload = json.load(handle)

    try:
        records = _coerce_payload(payload)
    except ValueError as exc:
        print(f"❌ {exc}")
        return 1

    factory_orders, telemetry_only, unsupported = _partition_records(records)
    lexicon = load_lexicon()

    order_schema_errors: List[str] = []
    order_dq_errors: List[str] = []
    for original_idx, order in factory_orders:
        result = validate_factory_order(order, lexicon)
        order_schema_errors.extend(
            f"Order[{original_idx}]: {err}" for err in result["schema_errors"]
        )
        order_dq_errors.extend(
            f"Order[{original_idx}]: {err}" for err in result["dq_errors"]
        )

    legacy_schema_errors, legacy_dq_errors = _validate_legacy_telemetry(telemetry_only)

    schema_errors = order_schema_errors + legacy_schema_errors
    if unsupported:
        schema_errors.append(
            f"Encountered {len(unsupported)} unsupported record(s) (non-object entries): {unsupported}"
        )

    if factory_orders:
        if order_schema_errors:
            print("  ✗ Factory-order schema validation failed:")
            for err in order_schema_errors[:10]:
                print(f"    - {err}")
            if len(order_schema_errors) > 10:
                print(f"    ... and {len(order_schema_errors) - 10} more errors")
        else:
            print(f"  ✓ Factory-order schema validation passed ({len(factory_orders)} records)")
    else:
        print("  • No factory-order@1.0 payloads detected")

    if telemetry_only:
        if legacy_schema_errors:
            print("  ✗ Legacy telemetry schema validation failed:")
            for err in legacy_schema_errors[:10]:
                print(f"    - {err}")
            if len(legacy_schema_errors) > 10:
                print(f"    ... and {len(legacy_schema_errors) - 10} more errors")
        else:
            print(f"  ✓ Legacy telemetry schema validation passed ({len(telemetry_only)} records)")
    else:
        print("  • No legacy telemetry records detected")

    # Step 3: Validate data quality
    print("\n[Step 3] Validating data quality thresholds...")
    dq_errors = order_dq_errors + legacy_dq_errors

    if order_dq_errors:
        print("  ✗ Factory-order data quality issues detected:")
        for err in order_dq_errors[:10]:
            print(f"    - {err}")
        if len(order_dq_errors) > 10:
            print(f"    ... and {len(order_dq_errors) - 10} more errors")
    elif factory_orders:
        print("  ✓ Factory-order data quality passed")

    if legacy_dq_errors:
        print("  ✗ Legacy telemetry data quality issues detected:")
        for err in legacy_dq_errors[:10]:
            print(f"    - {err}")
        if len(legacy_dq_errors) > 10:
            print(f"    ... and {len(legacy_dq_errors) - 10} more errors")
    elif telemetry_only:
        print("  ✓ Legacy telemetry data quality passed")

    # Step 4: Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    total_errors = len(checksum_errors) + len(schema_errors) + len(dq_errors)

    if total_errors == 0:
        print("✅ ACCEPT: All validations passed")
        print(f"   - Records validated: {len(records)}")
        print("   - SHA256 checks: PASS")
        print("   - Schema checks: PASS")
        print("   - Data-quality checks: PASS")
        return 0

    print("❌ REJECT: Validation failures detected")
    print(f"   - Checksum errors: {len(checksum_errors)}")
    print(f"   - Schema errors: {len(schema_errors)}")
    print(f"   - DQ errors: {len(dq_errors)}")
    print(f"   - Total errors: {total_errors}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
