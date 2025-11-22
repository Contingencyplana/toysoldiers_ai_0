"""
Hybrid comms block-end cadence runner.

Sequence:
- exchange_heartbeat
- offline_sync_exchange
- ops_readiness
- exchange_all

Purpose: one-button check for exchange health + readiness + sync hygiene.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_step(name: str, args: Sequence[str], *, env: Mapping[str, str] | None = None) -> None:
    """Run a single step and bubble up failures."""
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    cmd_display = " ".join(args)
    print(f"[{name}] {cmd_display}")
    result = subprocess.run(args, cwd=REPO_ROOT, env=merged_env)
    if result.returncode != 0:
        raise SystemExit(f"[{name}] failed with code {result.returncode}")


def main() -> None:
    py = sys.executable
    steps: Iterable[tuple[str, list[str], dict[str, str] | None]] = (
        ("heartbeat", [py, "tools/exchange_heartbeat.py"], None),
        ("offline_sync_exchange", [py, "tools/offline_sync_exchange.py"], {"PYTHONIOENCODING": "utf-8"}),
        ("ops_readiness", [py, "-m", "tools.ops_readiness"], None),
        ("exchange_all", [py, "tools/exchange_all.py"], None),
    )
    for name, args, extra_env in steps:
        run_step(name, args, env=extra_env)
    print("[end_of_block] cadence complete")


if __name__ == "__main__":
    main()
