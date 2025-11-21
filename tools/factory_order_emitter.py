"""Factory order emitter.

Transforms translator spike output into validated ``factory-order@1.0``
payloads and optionally applies overrides (order id, issuer, etc.). The tool
is intentionally lightweight so ops teams can run quick smoke checks via the
``--help`` path or produce ad-hoc payloads when coordinating with Toyfoundry.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emoji_translator import FACTORY_ORDER_SCHEMA, load_lexicon, validate_factory_order


def _load_translator_payload(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # noqa: BLE001
        raise ValueError(f"Translator payload {path} is invalid JSON: {exc}") from exc

    if isinstance(data, dict) and isinstance(data.get("payload"), dict):
        return data["payload"]
    if isinstance(data, dict):
        return data
    raise ValueError("Translator payload must be a JSON object")


def _parse_extra_field(token: str) -> Tuple[str, Any]:
    if "=" not in token:
        raise ValueError("extra-field entries must be in KEY=VALUE form")
    raw_key, raw_value = token.split("=", 1)
    key = raw_key.strip()
    if not key:
        raise ValueError("extra-field key cannot be empty")
    try:
        value = json.loads(raw_value)
    except json.JSONDecodeError:
        value = raw_value
    return key, value


def _apply_overrides(order: Dict[str, Any], args: argparse.Namespace) -> None:
    if args.order_id:
        order["order_id"] = args.order_id
    if args.issued_by:
        order["issued_by"] = args.issued_by
    if args.target:
        order["target"] = args.target
    if args.priority:
        order["priority"] = args.priority
    if args.timestamp:
        order["timestamp_issued"] = args.timestamp
    if args.summary:
        order["summary"] = args.summary
    if args.narrator:
        metadata = order.setdefault("metadata", {})
        metadata["narrator_profile"] = args.narrator
    for token in args.extra_field or []:
        key, value = _parse_extra_field(token)
        order[key] = value


def _validate(order: Dict[str, Any]) -> None:
    lexicon = load_lexicon()
    result = validate_factory_order(order, lexicon)
    if not result["accepted"]:
        schema_errors = result.get("schema_errors", [])
        dq_errors = result.get("dq_errors", [])
        if schema_errors:
            print("Schema errors:", file=sys.stderr)
            for err in schema_errors:
                print(f"  - {err}", file=sys.stderr)
        if dq_errors:
            print("Data-quality errors:", file=sys.stderr)
            for err in dq_errors:
                print(f"  - {err}", file=sys.stderr)
        raise SystemExit(1)


def emit(translator_payload: Path, destination: Path, args: argparse.Namespace) -> Dict[str, Any]:
    order = _load_translator_payload(translator_payload)
    order.setdefault("schema", FACTORY_ORDER_SCHEMA)
    _apply_overrides(order, args)
    _validate(order)

    if not args.dry_run:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(order, indent=2), encoding="utf-8")
        print(f"Wrote factory order -> {destination}")
    else:
        print(json.dumps(order, indent=2))
    return order


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Emit validated factory-order payloads")
    parser.add_argument("translator_payload", help="File containing translator spike output")
    parser.add_argument("destination", help="Where to write the factory-order JSON")
    parser.add_argument("--order-id", dest="order_id", help="Override order identifier")
    parser.add_argument("--issued-by", dest="issued_by", help="Override issuing workspace")
    parser.add_argument("--target", help="Override target workspace")
    parser.add_argument("--priority", help="Set priority flag")
    parser.add_argument("--timestamp", help="Override timestamp (ISO-8601)")
    parser.add_argument("--summary", help="Override lore summary")
    parser.add_argument("--narrator", help="Set metadata.narrator_profile")
    parser.add_argument(
        "--extra-field",
        action="append",
        help="Inject arbitrary KEY=VALUE assignments (VALUE parsed as JSON when possible)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview payload without writing")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    payload_path = Path(args.translator_payload).resolve()
    destination = Path(args.destination).resolve()

    try:
        emit(payload_path, destination, args)
    except Exception as exc:  # noqa: BLE001
        print(f"[factory_order_emitter] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())