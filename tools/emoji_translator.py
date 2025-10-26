"""Production emoji translator utilities for factory-order@1.0."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

ROOT = Path(__file__).parents[1]
LEXICON_PATH = ROOT / "planning" / "emoji_language" / "glyph_lexicon_level0.json"
DEFAULT_LOG = ROOT / "planning" / "emoji_language" / "spike_logs" / "translator_round_trips.jsonl"
FACTORY_ORDER_SCHEMA = "factory-order@1.0"

ALLOWED_RITUALS = {"forge", "drill", "parade", "purge", "promote"}
ALLOWED_STATUS = {"success", "warning", "error"}
DURATION_MIN = 0
DURATION_MAX = 300_000  # 5 minutes in ms


@dataclass(frozen=True)
class Glyph:
    category: str
    identifier: str
    emoji: str
    label: str
    extras: Dict[str, Any]


@dataclass(frozen=True)
class GlyphIndex:
    by_token: Dict[str, Glyph]
    by_id: Dict[str, Glyph]

    def get(self, token: str) -> Optional[Glyph]:
        return self.by_token.get(token)

    def get_by_id(self, glyph_id: str) -> Optional[Glyph]:
        return self.by_id.get(glyph_id)


def load_lexicon(path: Path | None = None) -> GlyphIndex:
    lexicon_path = path or LEXICON_PATH
    data = json.loads(lexicon_path.read_text(encoding="utf-8"))
    by_token: Dict[str, Glyph] = {}
    by_id: Dict[str, Glyph] = {}

    for category, entries in data.items():
        for entry in entries:
            glyph = Glyph(
                category=category,
                identifier=entry["id"],
                emoji=entry["emoji"],
                label=entry.get("label", entry["id"].title()),
                extras={k: v for k, v in entry.items() if k not in {"id", "emoji", "label"}},
            )
            by_token[glyph.emoji] = glyph
            by_token[glyph.identifier] = glyph
            by_id[glyph.identifier] = glyph

    return GlyphIndex(by_token=by_token, by_id=by_id)


def resolve_chain(tokens: Sequence[str], index: GlyphIndex) -> List[Glyph]:
    resolved: List[Glyph] = []
    for token in tokens:
        glyph = index.get(token)
        if glyph is None:
            raise ValueError(f"Unknown glyph token: {token}")
        resolved.append(glyph)
    return resolved


def derive_intent(chain: Sequence[Glyph]) -> Dict[str, Any]:
    if not chain:
        raise ValueError("Glyph chain is empty")

    actor = next((g for g in chain if g.category == "nouns"), None)
    if actor is None:
        raise ValueError("Glyph chain missing noun actor")

    action = next((g for g in chain if g.category == "verbs"), None)
    if action is None:
        raise ValueError("Glyph chain missing verb")

    remaining = [glyph for glyph in chain if glyph not in {actor, action}]
    target = next((g for g in remaining if g.category == "nouns"), None)
    qualifiers = [g for g in remaining if g.category == "qualifiers"]
    outcome = next((g for g in reversed(chain) if g.category == "outcomes"), None)

    return {
        "actor": actor,
        "action": action,
        "target": target,
        "qualifiers": qualifiers,
        "outcome": outcome,
    }


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


def build_summary(actor: Glyph, action: Glyph, target: Glyph | None, outcome: Glyph | None) -> str:
    target_text = target.label if target else "front"
    outcome_text = outcome.label if outcome else "Result"
    return f"{actor.label} {action.label.lower()}s the {target_text} → {outcome_text}"


def summary_from_intent(intent: Mapping[str, Optional[str]], index: GlyphIndex | None = None) -> str:
    glyphs = index or load_lexicon()
    actor = glyphs.get_by_id(intent.get("actor", "")) if intent.get("actor") else None
    action = glyphs.get_by_id(intent.get("action", "")) if intent.get("action") else None
    target = glyphs.get_by_id(intent.get("target", "")) if intent.get("target") else None
    outcome = glyphs.get_by_id(intent.get("outcome", "")) if intent.get("outcome") else None

    if actor is None or action is None:
        raise ValueError("Intent missing actor or action for summary generation")

    return build_summary(actor, action, target, outcome)


def build_order_payload(chain: Sequence[Glyph], intent: Mapping[str, Any]) -> Dict[str, Any]:
    actor: Glyph = intent["actor"]
    action: Glyph = intent["action"]
    target: Glyph | None = intent["target"]
    qualifiers: Sequence[Glyph] = intent["qualifiers"]
    outcome: Glyph | None = intent["outcome"]

    ritual = VERB_CANONICAL_RITUAL.get(action.identifier, "forge")
    status = OUTCOME_STATUS.get(outcome.identifier if outcome else "victory", "success")

    now = datetime.now(timezone.utc)
    telemetry = {
        "batch_id": f"{actor.identifier}-{action.identifier}-{now.strftime('%H%M%S')}",
        "ritual": ritual,
        "units_processed": max(1, len(chain)),
        "status": status,
        "duration_ms": 1000 + 250 * len(tuple(qualifiers)),
    }

    payload = {
        "schema": FACTORY_ORDER_SCHEMA,
        "summary": build_summary(actor, action, target, outcome),
        "glyph_chain": [glyph.emoji for glyph in chain],
        "intent": {
            "actor": actor.identifier,
            "action": action.identifier,
            "target": target.identifier if target else None,
            "qualifiers": [glyph.identifier for glyph in qualifiers],
            "outcome": outcome.identifier if outcome else None,
        },
        "telemetry_stub": telemetry,
    }

    return payload


def validate_telemetry_schema(records: Iterable[Mapping[str, Any]]) -> List[str]:
    errors: List[str] = []
    required_fields = {"batch_id", "ritual", "units_processed", "status", "duration_ms"}

    for idx, record in enumerate(records):
        missing = required_fields - set(record.keys())
        if missing:
            errors.append(f"Record {idx}: Missing fields {sorted(missing)}")

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


def validate_telemetry_dq(records: Iterable[Mapping[str, Any]]) -> List[str]:
    errors: List[str] = []

    for idx, record in enumerate(records):
        batch_id = record.get("batch_id", "")
        ritual = record.get("ritual", "")
        status = record.get("status", "")
        units = record.get("units_processed")
        duration = record.get("duration_ms")

        if not isinstance(batch_id, str) or not batch_id.strip():
            errors.append(f"Record {idx}: batch_id is empty")
        if not isinstance(ritual, str) or not ritual.strip():
            errors.append(f"Record {idx}: ritual is empty")
        if ritual and ritual not in ALLOWED_RITUALS:
            errors.append(f"Record {idx}: ritual '{ritual}' not in {sorted(ALLOWED_RITUALS)}")
        if status and status not in ALLOWED_STATUS:
            errors.append(f"Record {idx}: status '{status}' not in {sorted(ALLOWED_STATUS)}")
        if isinstance(units, int) and units < 0:
            errors.append(f"Record {idx}: units_processed {units} is negative")
        if isinstance(duration, int) and not (DURATION_MIN <= duration <= DURATION_MAX):
            errors.append(
                f"Record {idx}: duration_ms {duration} outside range [{DURATION_MIN}, {DURATION_MAX}]"
            )

    return errors


def validate_factory_order(order: Mapping[str, Any], index: GlyphIndex | None = None) -> Dict[str, Any]:
    schema_errors: List[str] = []
    dq_errors: List[str] = []
    lexicon = index or load_lexicon()

    if order.get("schema") != FACTORY_ORDER_SCHEMA:
        schema_errors.append(f"Order schema must be '{FACTORY_ORDER_SCHEMA}'")

    summary = order.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        schema_errors.append("Order summary must be a non-empty string")

    glyph_chain = order.get("glyph_chain")
    if not isinstance(glyph_chain, list) or not glyph_chain:
        schema_errors.append("glyph_chain must be a non-empty list")
    else:
        for idx, glyph in enumerate(glyph_chain):
            if not isinstance(glyph, str) or not glyph.strip():
                schema_errors.append(f"glyph_chain[{idx}] must be a non-empty string")

    intent_payload = order.get("intent")
    intent_complete = False
    if not isinstance(intent_payload, dict):
        schema_errors.append("intent must be an object")
    else:
        actor_id = intent_payload.get("actor")
        action_id = intent_payload.get("action")
        target_id = intent_payload.get("target")
        qualifiers_ids = intent_payload.get("qualifiers", [])
        outcome_id = intent_payload.get("outcome")

        required_ids = {
            "actor": actor_id,
            "action": action_id,
            "target": target_id,
            "outcome": outcome_id,
        }
        for key, value in required_ids.items():
            if value is not None and not isinstance(value, str):
                schema_errors.append(f"intent.{key} must be a string or null")

        if not isinstance(qualifiers_ids, list):
            schema_errors.append("intent.qualifiers must be a list")
        else:
            for idx, qualifier in enumerate(qualifiers_ids):
                if not isinstance(qualifier, str):
                    schema_errors.append(f"intent.qualifiers[{idx}] must be a string")

        actor = lexicon.get_by_id(actor_id) if isinstance(actor_id, str) else None
        action = lexicon.get_by_id(action_id) if isinstance(action_id, str) else None
        target = lexicon.get_by_id(target_id) if isinstance(target_id, str) else None
        outcome = lexicon.get_by_id(outcome_id) if isinstance(outcome_id, str) else None
        qualifiers = [lexicon.get_by_id(q) for q in qualifiers_ids] if isinstance(qualifiers_ids, list) else []

        if actor is None:
            schema_errors.append("intent.actor must reference a known glyph id")
        if action is None:
            schema_errors.append("intent.action must reference a known glyph id")
        if target_id is not None and target is None:
            schema_errors.append("intent.target must reference a known glyph id or be null")
        if outcome_id is not None and outcome is None:
            schema_errors.append("intent.outcome must reference a known glyph id or be null")
        for idx, qualifier in enumerate(qualifiers):
            if qualifier is None:
                schema_errors.append(f"intent.qualifiers[{idx}] must reference a known glyph id")

        intent_complete = actor is not None and action is not None

    telemetry = order.get("telemetry_stub")
    if not isinstance(telemetry, Mapping):
        schema_errors.append("telemetry_stub must be an object")
    else:
        schema_errors.extend(validate_telemetry_schema([telemetry]))
        dq_errors.extend(validate_telemetry_dq([telemetry]))

    if intent_complete and isinstance(intent_payload, dict) and isinstance(summary, str):
        try:
            expected_summary = summary_from_intent(intent_payload, lexicon)
        except ValueError as exc:
            dq_errors.append(str(exc))
        else:
            if expected_summary != summary:
                dq_errors.append(
                    "Narration summary mismatch: "
                    f"expected '{expected_summary}', got '{summary}'"
                )

    return {
        "schema_errors": schema_errors,
        "dq_errors": dq_errors,
        "accepted": not schema_errors and not dq_errors,
    }


def log_round_trip(log_path: Path, entry: Mapping[str, Any]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def translate_tokens(
    tokens: Sequence[str],
    index: GlyphIndex | None = None,
    log_path: Path | None = None,
) -> Dict[str, Any]:
    lexicon = index or load_lexicon()
    chain = resolve_chain(tokens, lexicon)
    intent = derive_intent(chain)
    payload = build_order_payload(chain, intent)
    validation = validate_factory_order(payload, lexicon)

    round_trip = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "glyphs": [glyph.emoji for glyph in chain],
        "intent": {
            "actor": intent["actor"].identifier,
            "action": intent["action"].identifier,
            "target": intent["target"].identifier if intent["target"] else None,
            "qualifiers": [glyph.identifier for glyph in intent["qualifiers"]],
            "outcome": intent["outcome"].identifier if intent["outcome"] else None,
        },
        "payload": payload,
        "validation": validation,
    }

    if log_path:
        log_round_trip(log_path, round_trip)

    return round_trip


def load_glyphs_from_file(path: Path) -> List[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    glyphs = payload.get("glyphs")
    if not isinstance(glyphs, list) or not glyphs:
        raise ValueError("Sample file missing glyph list")
    return [str(item) for item in glyphs]


__all__ = [
    "DEFAULT_LOG",
    "FACTORY_ORDER_SCHEMA",
    "Glyph",
    "GlyphIndex",
    "LEXICON_PATH",
    "load_glyphs_from_file",
    "load_lexicon",
    "log_round_trip",
    "resolve_chain",
    "translate_tokens",
    "validate_factory_order",
    "validate_telemetry_dq",
    "validate_telemetry_schema",
    "summary_from_intent",
]
