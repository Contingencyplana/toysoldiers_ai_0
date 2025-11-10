"""
Minimal contract test runner for Toysoldiers exchange.

Contracts included:
- json_validity: parse all JSON files under exchange/
- ledger_integrity: verify exchange/ledger/index.json paths exist

CLI:
- --list           List available contracts
- --select NAMES   Comma-separated or repeated names to run specific contracts
- -q/--quiet       Suppress per-file details; show summary only
- --failfast       Stop on first failing contract
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Tuple


# Make stdout robust on Windows consoles
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


RepoPath = Path(__file__).resolve().parents[1]
ExchangePath = RepoPath / "exchange"


def contract_json_validity(exchange_dir: Path, quiet: bool = False) -> Tuple[bool, str]:
    """Validate that all JSON files under exchange/ parse successfully."""
    if not exchange_dir.exists():
        return False, f"Missing exchange directory: {exchange_dir}"

    errors: List[str] = []
    for p in exchange_dir.rglob("*.json"):
        try:
            with p.open("r", encoding="utf-8") as f:
                json.load(f)
        except Exception as e:
            rel = p.relative_to(RepoPath)
            msg = f"ERR {rel}: {e}"
            errors.append(msg)
            if not quiet:
                print(msg)

    if errors:
        return False, f"json_validity: {len(errors)} file(s) invalid"
    return True, "json_validity: OK"


def contract_ledger_integrity(exchange_dir: Path, quiet: bool = False) -> Tuple[bool, str]:
    """Verify ledger paths exist for each order entry."""
    ledger = exchange_dir / "ledger" / "index.json"
    if not ledger.exists():
        return False, f"Missing ledger: {ledger}"

    try:
        with ledger.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return False, f"Failed to parse ledger: {e}"

    orders = (data or {}).get("orders", {})
    missing_count = 0
    for name, entry in orders.items():
        miss: List[str] = []
        for key in ("order_path", "ack_path", "report_path"):
            rel = entry.get(key)
            if not rel:
                miss.append(key)
                continue
            target = exchange_dir / rel
            if not target.exists():
                miss.append(key)
        if miss:
            missing_count += 1
            if not quiet:
                print(f"MISSING {name} -> {', '.join(miss)}")

    if missing_count:
        return False, f"ledger_integrity: {missing_count} order(s) with missing paths"
    return True, "ledger_integrity: OK"


ContractFn = Callable[[Path, bool], Tuple[bool, str]]

def contract_schema_checks(exchange_dir: Path, quiet: bool = False) -> Tuple[bool, str]:
    """Run schema validation for pending acks and inbox reports.

    Only validates folders that use supported schemas to avoid false negatives
    from historical payload formats.
    """
    # Import schema_validator via file path to avoid package layout issues
    import importlib.util
    validator_path = (RepoPath / "tools" / "schema_validator.py").resolve()
    try:
        spec = importlib.util.spec_from_file_location("schema_validator", str(validator_path))
        if spec is None or spec.loader is None:
            return False, "schema_checks: cannot load schema_validator spec"
        schema_validator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(schema_validator)  # type: ignore[attr-defined]
    except Exception as e:
        return False, f"schema_checks: cannot import validator -> {e}"

    # Collect candidate files and validate only supported schemas
    supported = {
        getattr(schema_validator, "SCHEMA_SIGNAL_ACK", "signal-ack@1.0"),
        getattr(schema_validator, "SCHEMA_FIELD_REPORT", "field-report@1.0"),
        getattr(schema_validator, "SCHEMA_FACTORY_REPORT", "factory-report@1.0"),
    }

    candidates: List[Path] = []
    for sub in [
        exchange_dir / "acknowledgements" / "pending",
        exchange_dir / "reports" / "inbox",
    ]:
        if sub.exists():
            candidates.extend(sorted(p for p in sub.glob("*.json") if p.is_file()))

    if not candidates:
        return True, "schema_checks: skipped (no targets)"

    failures = 0
    for path in candidates:
        try:
            payload = schema_validator._read_payload(path)  # type: ignore[attr-defined]
        except Exception as e:
            # Skip files that are not valid JSON at all; json_validity handles this.
            # Treat as a failure for schema contract clarity.
            failures += 1
            if not quiet:
                print(f"INVALID(JSON): {path} -> {e}")
            continue

        schema = payload.get("schema")
        if schema not in supported:
            # Not a schema we validate here; skip silently
            continue

        # Scope: default contract skips archived reports (legacy variability)

        try:
            schema_validator._validate_payload(payload)  # type: ignore[attr-defined]
            if not quiet:
                print(f"VALID: {path}")
        except Exception as e:
            failures += 1
            if not quiet:
                print(f"INVALID: {path} -> {e}")

    if failures:
        return False, f"schema_checks: {failures} failure(s)"
    return True, "schema_checks: OK"

CONTRACTS: Dict[str, Tuple[ContractFn, str]] = {
    "json_validity": (contract_json_validity, "Parse all JSON under exchange/"),
    "ledger_integrity": (contract_ledger_integrity, "Ensure ledger paths exist"),
    "schema_checks": (contract_schema_checks, "Validate pending acks + inbox reports"),
}


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(prog="contract_test_runner")
    ap.add_argument("--list", action="store_true", help="List available contracts")
    ap.add_argument(
        "--select",
        action="append",
        help="Comma-separated contract names to run (repeatable)",
    )
    ap.add_argument("-q", "--quiet", action="store_true", help="Reduce output noise")
    ap.add_argument("--failfast", action="store_true", help="Stop on first failure")
    return ap.parse_args(list(argv))


def iter_selected(names: List[str] | None) -> List[str]:
    if not names:
        return list(CONTRACTS.keys())
    sel: List[str] = []
    for chunk in names:
        for item in chunk.split(","):
            name = item.strip()
            if not name:
                continue
            sel.append(name)
    return sel


def main(argv: Iterable[str] = None) -> int:
    ns = parse_args(argv or sys.argv[1:])

    if ns.list:
        for name, (_, desc) in CONTRACTS.items():
            print(f"- {name}: {desc}")
        return 0

    selected = iter_selected(ns.select)
    unknown = [n for n in selected if n not in CONTRACTS]
    if unknown:
        print(f"Unknown contract(s): {', '.join(unknown)}", file=sys.stderr)
        print("Use --list to see available contracts.", file=sys.stderr)
        return 2

    failures = 0
    for name in selected:
        fn, _ = CONTRACTS[name]
        ok, msg = fn(ExchangePath, quiet=ns.quiet)
        if not ns.quiet:
            print(msg)
        if not ok:
            failures += 1
            if ns.failfast:
                break

    if failures:
        if not ns.quiet:
            print(f"Summary: {len(selected)-failures} passed, {failures} failed")
        return 1

    if not ns.quiet:
        print(f"Summary: {len(selected)} passed, 0 failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
