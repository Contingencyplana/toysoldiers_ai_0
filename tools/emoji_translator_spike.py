"""Emoji translator spike for Major Pivot Five.

Usage examples:
  python -m tools.emoji_translator_spike --glyphs "🛠️ ⚒️ 🤖 ✅"
  python -m tools.emoji_translator_spike --glyph-file samples/emoji_commands/level0_sample.json
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

from tools.validate_order_021 import validate_schema, validate_dq

ROOT = Path(__file__).parents[1]
LEXICON_PATH = ROOT / "planning" / "emoji_language" / "glyph_lexicon_level0.json"
DEFAULT_LOG = ROOT / "planning" / "emoji_language" / "spike_logs" / "translator_round_trips.jsonl"

VERB_CANONICAL_RITUAL: Dict[str, str] = {
    "craft": "forge",
    "launch": "parade",
    "grow": "promote",
    "shield": "purge",
    "weave": "forge",
    "loop": "drill",
    "deliver": "promote",
    "transmute": "forge",
}

OUTCOME_STATUS: Dict[str, str] = {
    "victory": "success",
    "risk": "warning",
    "sleep": "warning",
    "rise": "success",
    "chaos": "error",
    "blessing": "success",
    "pause": "warning",
    "repeat": "warning",
}


@dataclass(frozen=True)
class Glyph:
    category: str
    id: str
    emoji: str
    label: str
    extras: Dict[str, Any]


def load_lexicon(path: Path) -> Dict[str, Glyph]:
    data = json.loads(path.read_text(encoding="utf-8"))
    index: Dict[str, Glyph] = {}
    for category, entries in data.items():
        for entry in entries:
            glyph = Glyph(
                category=category,
                id=entry["id"],
                emoji=entry["emoji"],
                label=entry.get("label", entry["id"].title()),
                extras={k: v for k, v in entry.items() if k not in {"id", "emoji", "label"}},
            )
            index[glyph.emoji] = glyph
            index[glyph.id] = glyph
    return index


def resolve_chain(tokens: Sequence[str], index: Dict[str, Glyph]) -> List[Glyph]:
    resolved: List[Glyph] = []
    for token in tokens:
        glyph = index.get(token)
        if not glyph:
            raise ValueError(f"Unknown glyph token: {token}")
        resolved.append(glyph)
    return resolved


def derive_intent(chain: List[Glyph]) -> Dict[str, Any]:
    if not chain:
        raise ValueError("Glyph chain is empty")

    actor = next((g for g in chain if g.category == "nouns"), None)
    if not actor:
        raise ValueError("Glyph chain missing noun actor")

    verb = next((g for g in chain if g.category == "verbs"), None)
    if not verb:
        raise ValueError("Glyph chain missing verb")

    remaining = list(chain)
    remaining.remove(actor)
    remaining.remove(verb)
    target = next((g for g in remaining if g.category == "nouns"), None)
    qualifiers = [g for g in remaining if g.category == "qualifiers"]
    outcome = next((g for g in reversed(chain) if g.category == "outcomes"), None)

    return {
        "actor": actor,
        "action": verb,
        "target": target,
        "qualifiers": qualifiers,
        "outcome": outcome,
    }


def build_order_payload(chain: List[Glyph], intent: Dict[str, Any]) -> Dict[str, Any]:
    actor: Glyph = intent["actor"]
    action: Glyph = intent["action"]
    target: Glyph | None = intent["target"]
    qualifiers: List[Glyph] = intent["qualifiers"]
    outcome: Glyph | None = intent["outcome"]

    ritual = VERB_CANONICAL_RITUAL.get(action.id, "forge")
    status = OUTCOME_STATUS.get(outcome.id if outcome else "victory", "success")

    now = datetime.now(timezone.utc)
    record = {
        "batch_id": f"{actor.id}-{action.id}-{now.strftime('%H%M%S')}",
        "ritual": ritual,
        "units_processed": max(1, len(chain)),
        "status": status,
        "duration_ms": 1000 + 250 * len(qualifiers),
    }

    payload = {
        "schema": "factory-order@1.0",
    "summary": build_summary(actor, action, target, outcome),
        "glyph_chain": [g.emoji for g in chain],
        "intent": {
            "actor": actor.id,
            "action": action.id,
            "target": target.id if target else None,
            "qualifiers": [q.id for q in qualifiers],
            "outcome": outcome.id if outcome else None,
        },
        "telemetry_stub": record,
    }

    return payload


def build_summary(actor: Glyph, action: Glyph, target: Glyph | None, outcome: Glyph | None) -> str:
    target_text = target.label if target else "front"
    outcome_text = outcome.label if outcome else "Result"
    return f"{actor.label} {action.label.lower()}s the {target_text} → {outcome_text}"


def validate_payload(record: Dict[str, Any]) -> Dict[str, Any]:
    schema_errors = validate_schema([record])
    dq_errors = validate_dq([record])
    return {
        "schema_errors": schema_errors,
        "dq_errors": dq_errors,
        "accepted": not schema_errors and not dq_errors,
    }


def log_round_trip(log_path: Path, entry: Dict[str, Any]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Emoji translator spike prototype")
    parser.add_argument("--glyphs", help="Space-separated glyphs or ids", default=None)
    parser.add_argument("--glyph-file", help="Path to sample glyph JSON", default=None)
    parser.add_argument("--log", help="Log file path", default=str(DEFAULT_LOG))
    return parser.parse_args()


def load_glyphs_from_file(path: Path) -> List[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    glyphs = payload.get("glyphs")
    if not isinstance(glyphs, list) or not glyphs:
        raise ValueError("Sample file missing glyph list")
    return [str(item) for item in glyphs]


def main() -> int:
    args = parse_args()
    index = load_lexicon(LEXICON_PATH)

    if args.glyphs:
        tokens = args.glyphs.split()
    elif args.glyph_file:
        tokens = load_glyphs_from_file(Path(args.glyph_file))
    else:
        raise SystemExit("Provide --glyphs or --glyph-file")

    chain = resolve_chain(tokens, index)
    intent = derive_intent(chain)
    payload = build_order_payload(chain, intent)
    validation = validate_payload(payload["telemetry_stub"])

    round_trip = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "glyphs": [g.emoji for g in chain],
        "intent": {
            "actor": intent["actor"].id,
            "action": intent["action"].id,
            "target": intent["target"].id if intent["target"] else None,
            "qualifiers": [q.id for q in intent["qualifiers"]],
            "outcome": intent["outcome"].id if intent["outcome"] else None,
        },
        "payload": payload,
        "validation": validation,
    }

    log_round_trip(Path(args.log), round_trip)

    print(json.dumps(round_trip, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
