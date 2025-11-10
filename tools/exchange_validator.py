"""
exchange_validator.py - Thin wrapper to run exchange contracts.

Delegates to tools/contract_test_runner.py so that tools/exchange_all.py
can discover and invoke a validator consistently.

Usage examples:
- python tools/exchange_validator.py           # full run, verbose summary
- python tools/exchange_validator.py -q       # quiet summary
- python tools/exchange_validator.py --select schema_checks
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_runner(repo_root: Path):
    runner_path = repo_root / "tools" / "contract_test_runner.py"
    spec = importlib.util.spec_from_file_location("contract_test_runner", str(runner_path))
    if not spec or not spec.loader:
        return None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["contract_test_runner"] = mod
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


def main(argv: list[str] | None = None) -> int:
    repo_root = Path(__file__).resolve().parents[1]
    mod = _load_runner(repo_root)
    if not mod or not hasattr(mod, "main"):
        print("[ERROR] contract_test_runner not available")
        return 2
    # Pass through CLI args to the runner
    # When invoked from exchange_all.py, avoid leaking its CLI flags into the runner.
    # Pass a truthy empty Iterable so the runner does not fallback to sys.argv.
    empty_iter = iter(())
    return int(mod.main(argv if argv is not None else empty_iter))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
