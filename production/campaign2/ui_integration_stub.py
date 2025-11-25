"""Example UI integration for Campaign 2 emoji-first command layer.

Replace the `sample_events` source with real UI events. This shows how to call
CommandTelemetry so the UI emits consistent telemetry for Campaign 2.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Mapping

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from production.campaign2.command_layer import CommandTelemetry
from tools.emoji_translator import load_lexicon


def run_ui_integration(events: List[Mapping[str, any]], run_id: str) -> Dict[str, Path]:
    """Replay UI events through CommandTelemetry and persist outputs."""
    telemetry = CommandTelemetry(
        order_id="order-2025-11-26-061",
        workspace="toysoldiers_ai_0",
        run_id=run_id,
        lexicon=load_lexicon(),
    )

    for event in events:
        delta_ms = event["delta_ms"]
        etype = event["type"]
        if etype == "ui_state":
            telemetry.record_ui_state(event["state"], event.get("detail"), event.get("wheel"), event.get("player"), delta_ms)
        elif etype == "command":
            telemetry.record_command(
                source=event["source"],
                wheel=event["wheel"],
                slot=event["slot"],
                glyph_ids=event["glyph_ids"],
                player=event["player"],
                latency_ms=event["latency_ms"],
                label=event.get("label"),
                delta_ms=delta_ms,
            )
        elif etype == "downed":
            telemetry.record_downed(event["player"], event["by"], delta_ms)
        elif etype == "revive":
            telemetry.record_revive(event["player"], event["by"], event.get("emoji"), delta_ms)
        elif etype == "one_more_prompt":
            telemetry.record_one_more_prompt(event["accepted"], delta_ms)

    return telemetry.write_outputs(
        log_dir=Path("logs"),
        attachments_dir=Path("exchange/outbox/attachments/campaign2"),
        duration_ms=events[-1]["delta_ms"] if events else 0,
    )


if __name__ == "__main__":
    sample_events: List[Mapping[str, any]] = [
        {"delta_ms": 0, "type": "ui_state", "state": "tutorial_start", "detail": "UI stub"},
        {"delta_ms": 1500, "type": "ui_state", "state": "wheel_open", "wheel": "ability", "player": "P1"},
        {
            "delta_ms": 2800,
            "type": "command",
            "player": "P1",
            "source": "quick_cast",
            "wheel": "ability",
            "slot": "north",
            "glyph_ids": ["ally", "shield", "target"],
            "latency_ms": 220,
            "label": "Shield ally",
        },
        {"delta_ms": 4000, "type": "downed", "player": "P2", "by": "phantom"},
        {
            "delta_ms": 5200,
            "type": "command",
            "player": "P1",
            "source": "textless_comm",
            "wheel": "textless_comm",
            "slot": "revive_ping",
            "glyph_ids": ["ally", "deliver", "rise"],
            "latency_ms": 280,
            "label": "Revive call",
        },
        {
            "delta_ms": 7800,
            "type": "command",
            "player": "P1",
            "source": "quick_cast",
            "wheel": "ability",
            "slot": "north",
            "glyph_ids": ["ally", "shield", "seed"],
            "latency_ms": 420,
            "label": "Revive cast",
        },
        {"delta_ms": 7800, "type": "revive", "player": "P2", "by": "P1", "emoji": "ally+shield+seed"},
        {"delta_ms": 12000, "type": "one_more_prompt", "accepted": True},
    ]

    paths = run_ui_integration(sample_events, run_id="campaign2-ui-stub")
    print(f"Wrote events to {paths['events']}")
    print(f"Wrote telemetry to {paths['telemetry']}")
