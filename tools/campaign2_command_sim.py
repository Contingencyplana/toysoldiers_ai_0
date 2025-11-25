"""Simulate Campaign 2 emoji-first command layer with telemetry hooks."""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emoji_translator import GlyphIndex, load_lexicon, translate_tokens

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


@dataclass
class RoutedCommand:
    valid: bool
    intent: Optional[Mapping[str, Any]]
    error: Optional[str]


class EmojiCommandLayer:
    def __init__(self, lexicon: GlyphIndex) -> None:
        self.lexicon = lexicon

    def route(self, chain_ids: Sequence[str]) -> RoutedCommand:
        try:
            round_trip = translate_tokens(chain_ids, index=self.lexicon)
        except Exception as exc:  # translator raises ValueError on unknown glyphs
            return RoutedCommand(valid=False, intent=None, error=str(exc))

        return RoutedCommand(valid=True, intent=round_trip.get("intent"), error=None)


def ids_to_glyphs(chain_ids: Sequence[str], lexicon: GlyphIndex) -> List[str]:
    glyphs: List[str] = []
    for glyph_id in chain_ids:
        glyph = lexicon.get_by_id(glyph_id)
        glyphs.append(glyph.emoji if glyph else "<?>")
    return glyphs


def decorate_wheels(lexicon: GlyphIndex) -> List[Mapping[str, Any]]:
    wheels: List[Mapping[str, Any]] = []
    for wheel in QUICK_CAST_WHEELS:
        slots = []
        for slot in wheel["slots"]:
            glyph_ids = slot["glyph_ids"]
            slots.append(
                {
                    "slot": slot["slot"],
                    "label": slot["label"],
                    "glyph_ids": glyph_ids,
                    "glyphs": ids_to_glyphs(glyph_ids, lexicon),
                }
            )
        wheels.append({"wheel": wheel["wheel"], "slots": slots})
    return wheels


def percentile(values: Sequence[int], pct: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    k = int((len(ordered) - 1) * pct)
    return ordered[k]


def write_jsonl(path: Path, records: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def simulate_playtest(
    order_id: str,
    workspace: str,
    run_id: str,
    log_dir: Path,
    attachments_dir: Path,
    lexicon: GlyphIndex,
) -> Dict[str, Path]:
    start = datetime.now(timezone.utc)
    router = EmojiCommandLayer(lexicon)

    events: List[Mapping[str, Any]] = []
    latency_samples: List[Mapping[str, Any]] = []
    latencies_ms: List[int] = []
    total_commands = 0
    total_valid = 0
    downed_ms: Optional[int] = None
    revive_ms: Optional[int] = None
    first_valid_ms: Optional[int] = None

    for idx, step in enumerate(TUTORIAL_SCRIPT):
        event_time = start + timedelta(milliseconds=step["delta_ms"])
        timestamp = event_time.isoformat().replace("+00:00", "Z")

        if step["type"] == "command":
            total_commands += 1
            chain_ids = step["glyph_ids"]
            glyphs = ids_to_glyphs(chain_ids, lexicon)
            routed = router.route(chain_ids)
            valid = routed.valid
            if valid:
                total_valid += 1
                latencies_ms.append(step["latency_ms"])
                if first_valid_ms is None:
                    first_valid_ms = step["delta_ms"]
            command_event: Dict[str, Any] = {
                "type": "command",
                "event_id": f"cmd-{idx}",
                "timestamp": timestamp,
                "player": step["player"],
                "source": step["source"],
                "wheel": step["wheel"],
                "slot": step["slot"],
                "glyph_ids": chain_ids,
                "glyphs": glyphs,
                "latency_ms": step["latency_ms"],
                "label": step["label"],
                "valid": valid,
                "order_id": order_id,
                "run_id": run_id,
                "workspace": workspace,
            }
            if routed.intent:
                command_event["intent"] = routed.intent
            if routed.error:
                command_event["error"] = routed.error

            events.append(command_event)

            latency_event = {
                "type": "emoji_latency_sample",
                "event_id": f"latency-{idx}",
                "related_event": command_event["event_id"],
                "timestamp": timestamp,
                "player": step["player"],
                "glyph_ids": chain_ids,
                "glyphs": glyphs,
                "latency_ms": step["latency_ms"],
                "valid": valid,
                "order_id": order_id,
                "run_id": run_id,
                "workspace": workspace,
            }
            latency_samples.append(latency_event)
            events.append(latency_event)

        elif step["type"] == "downed":
            downed_ms = step["delta_ms"]
            events.append(
                {
                    "type": "downed",
                    "timestamp": timestamp,
                    "player": step["player"],
                    "by": step["by"],
                    "order_id": order_id,
                    "run_id": run_id,
                    "workspace": workspace,
                }
            )
        elif step["type"] == "revive":
            revive_ms = step["delta_ms"]
            events.append(
                {
                    "type": "revive",
                    "timestamp": timestamp,
                    "player": step["player"],
                    "by": step["by"],
                    "emoji": step.get("emoji"),
                    "order_id": order_id,
                    "run_id": run_id,
                    "workspace": workspace,
                }
            )
        elif step["type"] == "one_more_prompt":
            events.append(
                {
                    "type": "one_more_prompt",
                    "timestamp": timestamp,
                    "accepted": step["accepted"],
                    "order_id": order_id,
                    "run_id": run_id,
                    "workspace": workspace,
                }
            )
        elif step["type"] == "ui_state":
            events.append(
                {
                    "type": "ui_state",
                    "timestamp": timestamp,
                    "state": step["state"],
                    "detail": step.get("detail"),
                    "wheel": step.get("wheel"),
                    "player": step.get("player"),
                    "order_id": order_id,
                    "run_id": run_id,
                    "workspace": workspace,
                }
            )

    accuracy_rate = (total_valid / total_commands) if total_commands else 0
    avg_latency = int(statistics.mean(latencies_ms)) if latencies_ms else 0
    p95_latency = percentile(latencies_ms, 0.95)
    revive_gap_ms = revive_ms - downed_ms if downed_ms is not None and revive_ms is not None else None

    summary = {
        "schema": "toysoldiers-campaign2-telemetry@1.0",
        "order_id": order_id,
        "workspace": workspace,
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "metrics": {
            "time_to_fun_ms": first_valid_ms,
            "revive_ms": revive_gap_ms,
            "tutorial_duration_ms": TUTORIAL_SCRIPT[-1]["delta_ms"],
            "avg_command_latency_ms": avg_latency,
            "p95_command_latency_ms": p95_latency,
            "command_accuracy": round(accuracy_rate, 3),
            "commands_executed": total_commands,
            "commands_valid": total_valid,
            "one_more_accept": True,
        },
        "hud_signals": {
            "ui_state_events": len([e for e in events if e["type"] == "ui_state"]),
            "revive_events": len([e for e in events if e["type"] == "revive"]),
            "one_more_prompts": len([e for e in events if e["type"] == "one_more_prompt"]),
            "emoji_latency_samples": len(latency_samples),
        },
        "latency_samples": latency_samples,
        "guardrails": {
            "input_mode": "emoji_dsl_only",
            "filters": ["no free text", "template-bound commands", "wheel-locked quick-cast"],
            "non_emoji_inputs": [],
        },
        "quick_cast_wheels": decorate_wheels(lexicon),
    }

    events_path = log_dir / f"{order_id}-campaign2-playtest.jsonl"
    telemetry_path = log_dir / f"{order_id}-campaign2-telemetry.json"
    write_jsonl(events_path, events)
    write_json(telemetry_path, summary)

    attachments_dir.mkdir(parents=True, exist_ok=True)
    attachment_events = attachments_dir / events_path.name
    attachment_telemetry = attachments_dir / telemetry_path.name
    write_jsonl(attachment_events, events)
    write_json(attachment_telemetry, summary)

    return {"events": events_path, "telemetry": telemetry_path, "attachment_events": attachment_events, "attachment_telemetry": attachment_telemetry}


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
    lexicon = load_lexicon()
    paths = simulate_playtest(
        order_id=args.order_id,
        workspace=args.workspace,
        run_id=args.run_id,
        log_dir=Path(args.log_dir),
        attachments_dir=Path(args.attachments_dir),
        lexicon=lexicon,
    )
    print(f"Wrote events to {paths['events']}")
    print(f"Wrote telemetry to {paths['telemetry']}")


if __name__ == "__main__":
    main()
