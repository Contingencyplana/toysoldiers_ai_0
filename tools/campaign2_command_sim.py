"""Simulate Campaign 2 emoji-first command layer with reusable telemetry."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Mapping

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from production.campaign2.command_layer import CommandTelemetry
from tools.emoji_translator import load_lexicon

ORDER_ID_DEFAULT = "order-2025-11-26-061"
WORKSPACE_DEFAULT = "toysoldiers_ai_0"


QUICK_CAST_WHEELS: List[Mapping[str, Any]] = [
    {
        "wheel": "ability",
        "slots": [
            {"slot": "north", "glyph_ids": ["ally", "shield", "target"], "label": "Shield ally"},
            {"slot": "east", "glyph_ids": ["forge", "craft", "tempo"], "label": "Fast forge"},
            {"slot": "south", "glyph_ids": ["dream", "deliver", "idea"], "label": "Dream drop"},
            {"slot": "west", "glyph_ids": ["scout", "probe", "signal"], "label": "Scout ping"},
        ],
    },
    {
        "wheel": "textless_comm",
        "slots": [
            {"slot": "ping", "glyph_ids": ["ally", "deliver", "risk"], "label": "Danger ping"},
            {"slot": "revive_ping", "glyph_ids": ["ally", "deliver", "rise"], "label": "Revive call"},
            {"slot": "fallback", "glyph_ids": ["ally", "deliver", "fallback"], "label": "Fallback signal"},
        ],
    },
]


TUTORIAL_SCRIPT: List[Mapping[str, Any]] = [
    {"delta_ms": 0, "type": "ui_state", "state": "tutorial_start", "detail": "Emoji command layer warmup"},
    {"delta_ms": 1800, "type": "ui_state", "state": "wheel_open", "wheel": "ability", "player": "P1"},
    {
        "delta_ms": 3200,
        "type": "command",
        "player": "P1",
        "source": "quick_cast",
        "wheel": "ability",
        "slot": "north",
        "glyph_ids": ["ally", "shield", "target"],
        "latency_ms": 320,
        "label": "Shield ally",
    },
    {
        "delta_ms": 6200,
        "type": "command",
        "player": "P2",
        "source": "quick_cast",
        "wheel": "ability",
        "slot": "east",
        "glyph_ids": ["forge", "craft", "tempo"],
        "latency_ms": 410,
        "label": "Tempo forge",
    },
    {
        "delta_ms": 9200,
        "type": "command",
        "player": "P1",
        "source": "quick_cast",
        "wheel": "textless_comm",
        "slot": "ping",
        "glyph_ids": ["ally", "deliver", "risk"],
        "latency_ms": 280,
        "label": "Danger ping",
    },
    {
        "delta_ms": 14200,
        "type": "command",
        "player": "P2",
        "source": "quick_cast",
        "wheel": "ability",
        "slot": "south",
        "glyph_ids": ["dream", "deliver", "idea"],
        "latency_ms": 540,
        "label": "Dream drop",
    },
    {
        "delta_ms": 18200,
        "type": "command",
        "player": "P1",
        "source": "quick_cast",
        "wheel": "ability",
        "slot": "west",
        "glyph_ids": ["scout", "probe", "signal"],
        "latency_ms": 360,
        "label": "Scout ping",
    },
    {
        "delta_ms": 22600,
        "type": "command",
        "player": "P2",
        "source": "quick_cast",
        "wheel": "ability",
        "slot": "north",
        "glyph_ids": ["ally", "shield", "unknown_token"],
        "latency_ms": 480,
        "label": "Rejected guardrail sample",
    },
    {"delta_ms": 32000, "type": "downed", "player": "P2", "by": "phantom"},
    {
        "delta_ms": 35200,
        "type": "command",
        "player": "P1",
        "source": "textless_comm",
        "wheel": "textless_comm",
        "slot": "revive_ping",
        "glyph_ids": ["ally", "deliver", "rise"],
        "latency_ms": 300,
        "label": "Revive call",
    },
    {
        "delta_ms": 46600,
        "type": "command",
        "player": "P1",
        "source": "quick_cast",
        "wheel": "ability",
        "slot": "north",
        "glyph_ids": ["ally", "shield", "seed"],
        "latency_ms": 620,
        "label": "Revive cast",
    },
    {"delta_ms": 46600, "type": "revive", "player": "P2", "by": "P1", "emoji": "ally+shield+seed"},
    {
        "delta_ms": 60200,
        "type": "command",
        "player": "P2",
        "source": "quick_cast",
        "wheel": "ability",
        "slot": "east",
        "glyph_ids": ["forge", "craft", "tempo"],
        "latency_ms": 350,
        "label": "Tempo forge repeat",
    },
    {
        "delta_ms": 74000,
        "type": "command",
        "player": "P1",
        "source": "quick_cast",
        "wheel": "textless_comm",
        "slot": "fallback",
        "glyph_ids": ["ally", "deliver", "fallback"],
        "latency_ms": 330,
        "label": "Fallback signal",
    },
    {"delta_ms": 82000, "type": "ui_state", "state": "tutorial_checkpoint", "detail": "Ready for looped runs"},
    {"delta_ms": 90000, "type": "one_more_prompt", "accepted": True},
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Campaign 2 emoji command layer simulator")
    parser.add_argument("--order-id", default=ORDER_ID_DEFAULT, help="Order id to stamp into logs")
    parser.add_argument("--workspace", default=WORKSPACE_DEFAULT, help="Workspace id stamped into logs")
    parser.add_argument("--run-id", default=f"campaign2-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}", help="Run id for this playtest")
    parser.add_argument("--log-dir", default="logs", help="Directory to write log outputs")
    parser.add_argument(
        "--attachments-dir",
        default="exchange/outbox/attachments/campaign2",
        help="Directory to mirror attachment outputs",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    telemetry = CommandTelemetry(
        order_id=args.order_id,
        workspace=args.workspace,
        run_id=args.run_id,
        lexicon=load_lexicon(),
    )

    for step in TUTORIAL_SCRIPT:
        delta_ms = step["delta_ms"]
        if step["type"] == "ui_state":
            telemetry.record_ui_state(step["state"], step.get("detail"), step.get("wheel"), step.get("player"), delta_ms)
        elif step["type"] == "command":
            telemetry.record_command(
                source=step["source"],
                wheel=step["wheel"],
                slot=step["slot"],
                glyph_ids=step["glyph_ids"],
                player=step["player"],
                latency_ms=step["latency_ms"],
                label=step.get("label"),
                delta_ms=delta_ms,
            )
        elif step["type"] == "downed":
            telemetry.record_downed(step["player"], step["by"], delta_ms)
        elif step["type"] == "revive":
            telemetry.record_revive(step["player"], step["by"], step.get("emoji"), delta_ms)
        elif step["type"] == "one_more_prompt":
            telemetry.record_one_more_prompt(step["accepted"], delta_ms)

    paths = telemetry.write_outputs(
        log_dir=Path(args.log_dir),
        attachments_dir=Path(args.attachments_dir),
        duration_ms=TUTORIAL_SCRIPT[-1]["delta_ms"],
    )
    print(f"Wrote events to {paths['events']}")
    print(f"Wrote telemetry to {paths['telemetry']}")


if __name__ == "__main__":
    main()
