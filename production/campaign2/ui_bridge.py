"""UI bridge for Campaign 2: route live UI events through CommandTelemetry.

Use this module inside the actual UI input handlers. It binds wheel slots to
glyph ids and exposes convenience methods to log UI state, commands, revives,
and the one-more prompt. Outputs land in logs/ and exchange/outbox/attachments/campaign2/.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

from production.campaign2.command_layer import CommandTelemetry
from tools.emoji_translator import load_lexicon


WHEEL_BINDINGS: Dict[str, Dict[str, Sequence[str]]] = {
    "ability": {
        "north": ["ally", "shield", "target"],  # Shield ally
        "east": ["forge", "craft", "tempo"],  # Fast/tempo forge
        "south": ["dream", "deliver", "idea"],  # Dream drop
        "west": ["scout", "probe", "signal"],  # Scout ping
    },
    "textless_comm": {
        "ping": ["ally", "deliver", "risk"],  # Danger ping
        "revive_ping": ["ally", "deliver", "rise"],  # Revive call
        "fallback": ["ally", "deliver", "fallback"],  # Fallback signal
    },
}


def default_run_id(prefix: str = "campaign2-live") -> str:
    return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"


@dataclass
class UILoggingSession:
    run_id: str
    order_id: str = "order-2025-11-26-061"
    workspace: str = "toysoldiers_ai_0"
    telemetry: CommandTelemetry = field(init=False)

    def __post_init__(self) -> None:
        self.telemetry = CommandTelemetry(
            order_id=self.order_id,
            workspace=self.workspace,
            run_id=self.run_id,
            lexicon=load_lexicon(),
        )

    def wheel_open(self, wheel: str, player: str, detail: str | None, delta_ms: int) -> None:
        self.telemetry.record_ui_state("wheel_open", detail, wheel, player, delta_ms)

    def ui_state(self, state: str, detail: str | None, wheel: str | None, player: str | None, delta_ms: int) -> None:
        self.telemetry.record_ui_state(state, detail, wheel, player, delta_ms)

    def cast(self, wheel: str, slot: str, player: str, latency_ms: int, delta_ms: int, label: str | None = None) -> None:
        glyph_ids = WHEEL_BINDINGS.get(wheel, {}).get(slot, [])
        self.telemetry.record_command(
            source="quick_cast" if wheel == "ability" else "textless_comm",
            wheel=wheel,
            slot=slot,
            glyph_ids=glyph_ids,
            player=player,
            latency_ms=latency_ms,
            label=label,
            delta_ms=delta_ms,
        )

    def downed(self, player: str, by: str, delta_ms: int) -> None:
        self.telemetry.record_downed(player, by, delta_ms)

    def revive(self, player: str, by: str, emoji: str | None, delta_ms: int) -> None:
        self.telemetry.record_revive(player, by, emoji, delta_ms)

    def one_more(self, accepted: bool, delta_ms: int) -> None:
        self.telemetry.record_one_more_prompt(accepted, delta_ms)

    def finalize(self, duration_ms: int, log_dir: Path | str = "logs", attachments_dir: Path | str = "exchange/outbox/attachments/campaign2") -> Mapping[str, Any]:
        return self.telemetry.write_outputs(
            log_dir=Path(log_dir),
            attachments_dir=Path(attachments_dir),
            duration_ms=duration_ms,
        )
