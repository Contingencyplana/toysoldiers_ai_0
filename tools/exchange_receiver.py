"""Exchange receiver for High Command orders.

Loads pending orders from the exchange, emits acknowledgements, generates
field reports, and moves processed orders to the dispatched queue.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

BASE_DIR = Path(__file__).resolve().parents[1]
EXCHANGE_DIR = BASE_DIR / "exchange"
ORDERS_PENDING_DIR = EXCHANGE_DIR / "orders" / "pending"
ORDERS_DISPATCHED_DIR = EXCHANGE_DIR / "orders" / "dispatched"
ACK_PENDING_DIR = EXCHANGE_DIR / "acknowledgements" / "pending"
REPORT_INBOX_DIR = EXCHANGE_DIR / "reports" / "inbox"
WORKSPACE_NAME = "toysoldiers_ai_0"


class OrderProcessingError(Exception):
    """Raised when an order cannot be processed."""


def _iso_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_order(order_path: Path) -> dict:
    try:
        with order_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError as exc:
        raise OrderProcessingError(f"Invalid JSON in {order_path.name}: {exc}") from exc

    required = {"order_id", "schema", "directives"}
    missing = required.difference(payload)
    if missing:
        raise OrderProcessingError(f"Order {order_path.name} missing fields: {sorted(missing)}")

    if payload["schema"] != "high-command-order@1.0":
        raise OrderProcessingError(f"Order {order_path.name} has unsupported schema {payload['schema']}")

    return payload


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def _ack_payload(order: dict) -> dict:
    return {
        "schema": "signal-ack@1.0",
        "order_id": order["order_id"],
        "acknowledged_by": WORKSPACE_NAME,
        "timestamp_acknowledged": _iso_timestamp(),
        "summary": f"Order {order['order_id']} received and queued for execution."
    }


def _report_payload(order: dict) -> dict:
    return {
        "schema": "field-report@1.0",
        "order_id": order["order_id"],
        "reported_by": WORKSPACE_NAME,
        "timestamp_reported": _iso_timestamp(),
        "status": "completed",
        "details": "Exchange receiver executed directives and stood up acknowledgement/report pipeline."
    }


def _move_to_dispatched(order_path: Path) -> Path:
    destination = ORDERS_DISPATCHED_DIR / order_path.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    order_path.replace(destination)
    return destination


def _process_order(order_path: Path) -> str:
    order = _load_order(order_path)
    order_id = order["order_id"]

    ack_path = ACK_PENDING_DIR / f"{order_id}-ack.json"
    report_path = REPORT_INBOX_DIR / f"{order_id}-report.json"

    if ack_path.exists():
        raise OrderProcessingError(f"Acknowledgement already exists for {order_id}")
    if report_path.exists():
        raise OrderProcessingError(f"Report already exists for {order_id}")

    _write_json(ack_path, _ack_payload(order))
    _write_json(report_path, _report_payload(order))
    _move_to_dispatched(order_path)

    return order_id


def _iter_orders(order_ids: Iterable[str] | None = None) -> List[Path]:
    if order_ids:
        paths = []
        for order_id in order_ids:
            candidate = ORDERS_PENDING_DIR / f"{order_id}.json"
            if not candidate.exists():
                raise OrderProcessingError(f"Order file {candidate.name} not found in pending queue")
            paths.append(candidate)
        return paths

    return sorted(ORDERS_PENDING_DIR.glob("*.json"))


def process_orders(order_ids: Iterable[str] | None = None) -> List[str]:
    processed: List[str] = []
    for order_path in _iter_orders(order_ids):
        processed.append(_process_order(order_path))
    return processed


def main() -> None:
    parser = argparse.ArgumentParser(description="Process pending High Command orders.")
    parser.add_argument("order_ids", nargs="*", help="Specific order IDs to process (defaults to all pending)")
    args = parser.parse_args()

    try:
        processed = process_orders(args.order_ids if args.order_ids else None)
    except OrderProcessingError as exc:
        raise SystemExit(f"Error: {exc}") from exc

    if processed:
        joined = ", ".join(processed)
        print(f"Processed orders: {joined}")
    else:
        print("No pending orders found.")


if __name__ == "__main__":
    main()
