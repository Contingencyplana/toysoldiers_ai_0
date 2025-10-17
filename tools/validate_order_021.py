"""
Order 021: Consumer roll-in validation for Toyfoundry standard run.

Validates:
- SHA256 checksums from export_manifest.json
- Schema version v1.0
- Field/type/nullability/enum invariants
- DQ thresholds: non_empty, allowed_rituals/status, units_positive, duration_ms_range
"""
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple

IMPORTS_DIR = Path(__file__).parents[1] / ".imports" / "toyfoundry" / "telemetry" / "quilt" / "exports"
SCHEMA_VERSION = "v1.0"

ALLOWED_RITUALS = {"forge", "drill", "parade", "purge", "promote"}
ALLOWED_STATUS = {"success", "warning", "error"}
DURATION_MIN = 0
DURATION_MAX = 300000  # 5 minutes in ms


def validate_sha256(file_path: Path, expected_hash: str) -> Tuple[bool, str]:
    """Verify SHA256 checksum."""
    if not file_path.exists():
        return False, f"File not found: {file_path}"
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    actual = sha256_hash.hexdigest()
    if actual != expected_hash:
        return False, f"Hash mismatch: expected {expected_hash}, got {actual}"
    
    return True, "OK"


def validate_schema(data: List[Dict]) -> List[str]:
    """Validate schema v1.0 invariants."""
    errors = []
    required_fields = {"batch_id", "ritual", "units_processed", "status", "duration_ms"}
    
    for idx, record in enumerate(data):
        # Check required fields
        missing = required_fields - set(record.keys())
        if missing:
            errors.append(f"Record {idx}: Missing fields {missing}")
        
        # Check field types
        if "batch_id" in record and not isinstance(record["batch_id"], str):
            errors.append(f"Record {idx}: batch_id must be string")
        if "ritual" in record and not isinstance(record["ritual"], str):
            errors.append(f"Record {idx}: ritual must be string")
        if "units_processed" in record and not isinstance(record["units_processed"], int):
            errors.append(f"Record {idx}: units_processed must be integer")
        if "status" in record and not isinstance(record["status"], str):
            errors.append(f"Record {idx}: status must be string")
        if "duration_ms" in record and not isinstance(record["duration_ms"], int):
            errors.append(f"Record {idx}: duration_ms must be integer")
    
    return errors


def validate_dq(data: List[Dict]) -> List[str]:
    """Validate data quality thresholds."""
    errors = []
    
    for idx, record in enumerate(data):
        # non_empty checks
        if not record.get("batch_id", "").strip():
            errors.append(f"Record {idx}: batch_id is empty")
        if not record.get("ritual", "").strip():
            errors.append(f"Record {idx}: ritual is empty")
        
        # allowed_enums
        ritual = record.get("ritual", "")
        if ritual and ritual not in ALLOWED_RITUALS:
            errors.append(f"Record {idx}: ritual '{ritual}' not in {ALLOWED_RITUALS}")
        
        status = record.get("status", "")
        if status and status not in ALLOWED_STATUS:
            errors.append(f"Record {idx}: status '{status}' not in {ALLOWED_STATUS}")
        
        # units_positive
        units = record.get("units_processed")
        if units is not None and units < 0:
            errors.append(f"Record {idx}: units_processed {units} is negative")
        
        # duration_ms_range
        duration = record.get("duration_ms")
        if duration is not None:
            if duration < DURATION_MIN or duration > DURATION_MAX:
                errors.append(f"Record {idx}: duration_ms {duration} outside range [{DURATION_MIN}, {DURATION_MAX}]")
    
    return errors


def main():
    print("=" * 60)
    print("ORDER 021: Consumer Validation for Standard Run")
    print("=" * 60)
    
    # Step 1: Verify SHA256 checksums
    print("\n[Step 1] Verifying SHA256 checksums...")
    manifest_path = IMPORTS_DIR / "export_manifest.json"
    
    if not manifest_path.exists():
        print(f"❌ export_manifest.json not found at {manifest_path}")
        return 1
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    checksum_errors = []
    for artifact in manifest.get("artifacts", []):
        file_path = IMPORTS_DIR / artifact["filename"]
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
    
    # Step 2: Validate schema v1.0
    print(f"\n[Step 2] Validating schema {SCHEMA_VERSION}...")
    composite_json = IMPORTS_DIR / "composite_export.json"
    
    if not composite_json.exists():
        print(f"❌ composite_export.json not found")
        return 1
    
    with open(composite_json) as f:
        data = json.load(f)
    
    schema_errors = validate_schema(data)
    if schema_errors:
        print(f"  ✗ Schema validation failed:")
        for err in schema_errors[:10]:  # Show first 10
            print(f"    - {err}")
        if len(schema_errors) > 10:
            print(f"    ... and {len(schema_errors) - 10} more errors")
    else:
        print(f"  ✓ Schema validation passed ({len(data)} records)")
    
    # Step 3: Validate DQ thresholds
    print("\n[Step 3] Validating data quality thresholds...")
    dq_errors = validate_dq(data)
    if dq_errors:
        print(f"  ✗ DQ validation failed:")
        for err in dq_errors[:10]:
            print(f"    - {err}")
        if len(dq_errors) > 10:
            print(f"    ... and {len(dq_errors) - 10} more errors")
    else:
        print(f"  ✓ DQ validation passed")
    
    # Step 4: Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    total_errors = len(checksum_errors) + len(schema_errors) + len(dq_errors)
    
    if total_errors == 0:
        print("✅ ACCEPT: All validations passed")
        print(f"   - Records validated: {len(data)}")
        print(f"   - SHA256 checks: PASS")
        print(f"   - Schema v1.0: PASS")
        print(f"   - DQ thresholds: PASS")
        return 0
    else:
        print("❌ REJECT: Validation failures detected")
        print(f"   - Checksum errors: {len(checksum_errors)}")
        print(f"   - Schema errors: {len(schema_errors)}")
        print(f"   - DQ errors: {len(dq_errors)}")
        print(f"   - Total errors: {total_errors}")
        return 1


if __name__ == "__main__":
    exit(main())
