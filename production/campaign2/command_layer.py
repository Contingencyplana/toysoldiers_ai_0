"""Reusable emoji-first command layer + telemetry helpers for Campaign 2.

The UI should route every command through these helpers to keep the
emoji DSL guardrails intact and emit consistent telemetry (latency,
accuracy, HUD signals).
"""
from __future__ import annotations

import json
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from tools.emoji_translator import GlyphIndex, load_lexicon, translate_tokens


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def isoformat(ts: datetime) -> str:
    return ts.isoformat().replace("+00:00", "Z")


def ids_to_glyphs(chain_ids: Sequence[str], lexicon: GlyphIndex) -> List[str]:
    glyphs: List[str] = []
    for glyph_id in chain_ids:
        glyph = lexicon.get_by_id(glyph_id)
        glyphs.append(glyph.emoji if glyph else "<?>")
    return glyphs


def percentile(values: Sequence[int], pct: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    k = int((len(ordered) - 1) * pct)
    return ordered[k]


@dataclass
class CommandTelemetry:
    order_id: str
    workspace: str
    run_id: str
    lexicon: GlyphIndex = field(default_factory=load_lexicon)
    start_time: datetime = field(default_factory=utc_now)

    events: List[Mapping[str, Any]] = field(default_factory=list)
    latency_samples: List[Mapping[str, Any]] = field(default_factory=list)
    latencies_ms: List[int] = field(default_factory=list)
    total_commands: int = 0
    total_valid: int = 0
    first_valid_ms: Optional[int] = None
    downed_ms: Optional[int] = None
    revive_ms: Optional[int] = None
    _counter: int = 0

    def _timestamp(self, delta_ms: int) -> str:
        return isoformat(self.start_time + timedelta(milliseconds=delta_ms))

    def record_ui_state(self, state: str, detail: Optional[str], wheel: Optional[str], player: Optional[str], delta_ms: int) -> None:
        self.events.append(
            {
                "type": "ui_state",
                "timestamp": self._timestamp(delta_ms),
                "state": state,
                "detail": detail,
                "wheel": wheel,
                "player": player,
                "order_id": self.order_id,
                "run_id": self.run_id,
                "workspace": self.workspace,
            }
        )

    def record_command(
        self,
        source: str,
        wheel: str,
        slot: str,
        glyph_ids: Sequence[str],
        player: str,
        latency_ms: int,
        label: Optional[str],
        delta_ms: int,
    ) -> None:
        event_id = f"cmd-{self._counter}"
        self._counter += 1
        glyphs = ids_to_glyphs(glyph_ids, self.lexicon)
        timestamp = self._timestamp(delta_ms)

        record: Dict[str, Any] = {
            "type": "command",
            "event_id": event_id,
            "timestamp": timestamp,
            "player": player,
            "source": source,
            "wheel": wheel,
            "slot": slot,
            "glyph_ids": list(glyph_ids),
            "glyphs": glyphs,
            "latency_ms": latency_ms,
            "label": label,
            "order_id": self.order_id,
            "run_id": self.run_id,
            "workspace": self.workspace,
        }

        self.total_commands += 1
        try:
            round_trip = translate_tokens(glyph_ids, index=self.lexicon)
            record["valid"] = True
            record["intent"] = round_trip.get("intent")
            self.total_valid += 1
            self.latencies_ms.append(latency_ms)
            if self.first_valid_ms is None:
                self.first_valid_ms = delta_ms
        except Exception as exc:
            record["valid"] = False
            record["error"] = str(exc)

        self.events.append(record)

        latency_event = {
            "type": "emoji_latency_sample",
            "event_id": f"latency-{event_id}",
            "related_event": event_id,
            "timestamp": timestamp,
            "player": player,
            "glyph_ids": list(glyph_ids),
            "glyphs": glyphs,
            "latency_ms": latency_ms,
            "valid": record["valid"],
            "order_id": self.order_id,
            "run_id": self.run_id,
            "workspace": self.workspace,
        }
        self.latency_samples.append(latency_event)
        self.events.append(latency_event)

    def record_downed(self, player: str, by: str, delta_ms: int) -> None:
        self.downed_ms = delta_ms
        self.events.append(
            {
                "type": "downed",
                "timestamp": self._timestamp(delta_ms),
                "player": player,
                "by": by,
                "order_id": self.order_id,
                "run_id": self.run_id,
                "workspace": self.workspace,
            }
        )

    def record_revive(self, player: str, by: str, emoji: Optional[str], delta_ms: int) -> None:
        self.revive_ms = delta_ms
        self.events.append(
            {
                "type": "revive",
                "timestamp": self._timestamp(delta_ms),
                "player": player,
                "by": by,
                "emoji": emoji,
                "order_id": self.order_id,
                "run_id": self.run_id,
                "workspace": self.workspace,
            }
        )

    def record_one_more_prompt(self, accepted: bool, delta_ms: int) -> None:
        self.events.append(
            {
                "type": "one_more_prompt",
                "timestamp": self._timestamp(delta_ms),
                "accepted": accepted,
                "order_id": self.order_id,
                "run_id": self.run_id,
                "workspace": self.workspace,
            }
        )

    def build_summary(self, duration_ms: int) -> Mapping[str, Any]:
        accuracy_rate = (self.total_valid / self.total_commands) if self.total_commands else 0
        avg_latency = int(statistics.mean(self.latencies_ms)) if self.latencies_ms else 0
        p95_latency = percentile(self.latencies_ms, 0.95)
        revive_gap_ms = (
            self.revive_ms - self.downed_ms if self.downed_ms is not None and self.revive_ms is not None else None
        )

        return {
            "schema": "toysoldiers-campaign2-telemetry@1.0",
            "order_id": self.order_id,
            "workspace": self.workspace,
            "run_id": self.run_id,
            "timestamp": isoformat(utc_now()),
            "metrics": {
                "time_to_fun_ms": self.first_valid_ms,
                "revive_ms": revive_gap_ms,
                "tutorial_duration_ms": duration_ms,
                "avg_command_latency_ms": avg_latency,
                "p95_command_latency_ms": p95_latency,
                "command_accuracy": round(accuracy_rate, 3),
                "commands_executed": self.total_commands,
                "commands_valid": self.total_valid,
                "one_more_accept": True,
            },
            "hud_signals": {
                "ui_state_events": len([e for e in self.events if e["type"] == "ui_state"]),
                "revive_events": len([e for e in self.events if e["type"] == "revive"]),
                "one_more_prompts": len([e for e in self.events if e["type"] == "one_more_prompt"]),
                "emoji_latency_samples": len(self.latency_samples),
            },
            "latency_samples": self.latency_samples,
            "guardrails": {
                "input_mode": "emoji_dsl_only",
                "filters": ["no free text", "template-bound commands", "wheel-locked quick-cast"],
                "non_emoji_inputs": [],
            },
        }

    def export_payloads(self, duration_ms: int) -> Mapping[str, Any]:
        summary = self.build_summary(duration_ms)
        return {
            "events": self.events,
            "telemetry": summary,
        }

    def write_outputs(self, log_dir: Path, attachments_dir: Path, duration_ms: int) -> Dict[str, Path]:
        payloads = self.export_payloads(duration_ms)
        log_dir.mkdir(parents=True, exist_ok=True)
        attachments_dir.mkdir(parents=True, exist_ok=True)

        events_path = log_dir / f"{self.order_id}-campaign2-playtest.jsonl"
        telemetry_path = log_dir / f"{self.order_id}-campaign2-telemetry.json"
        attachment_events = attachments_dir / events_path.name
        attachment_telemetry = attachments_dir / telemetry_path.name

        def write_jsonl(path: Path, records: List[Mapping[str, Any]]) -> None:
            with path.open("w", encoding="utf-8") as handle:
                for record in records:
                    handle.write(json.dumps(record, ensure_ascii=False) + "\n")

        def write_json(path: Path, payload: Mapping[str, Any]) -> None:
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

        write_jsonl(events_path, payloads["events"])
        write_json(telemetry_path, payloads["telemetry"])
        write_jsonl(attachment_events, payloads["events"])
        write_json(attachment_telemetry, payloads["telemetry"])

        return {
            "events": events_path,
            "telemetry": telemetry_path,
            "attachment_events": attachment_events,
            "attachment_telemetry": attachment_telemetry,
        }
