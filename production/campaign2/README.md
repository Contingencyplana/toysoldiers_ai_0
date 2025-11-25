# Campaign 2 - Emoji-First Command Layer (Toysoldiers)

Goals for order-2025-11-26-061:
- Route UI inputs through the emoji DSL guardrails (quick-cast wheels + textless comms) and surface HUD changes from DSL actions.
- Deliver a replayable ~90s emoji-only tutorial that drills core commands.
- Instrument command latency/accuracy plus HUD signals (ui_state, revive cadence, one_more_prompt, emoji_latency_sample).

Quick-cast layout (DSL-aligned):
- ability wheel: north=ally+shield+target, east=forge+craft+tempo, south=dream+deliver+idea, west=scout+probe+signal.
- textless_comm wheel: ping=ally+deliver+risk, revive_ping=ally+deliver+rise, fallback=ally+deliver+fallback.
- Guardrails: emoji-only inputs, wheel-locked options, translator validation via tools/emoji_translator.py.

Telemetry slice:
- Router/telemetry helper: `production/campaign2/command_layer.py` exposes `CommandTelemetry`, which the UI should call for every command/UI event.
- Simulator: `python tools/campaign2_command_sim.py --run-id campaign2-playtest`.
- Outputs (mirrored to logs/ and exchange/outbox/attachments/campaign2/):
  - `order-2025-11-26-061-campaign2-playtest.jsonl` (ui_state, command, revive, one_more_prompt, emoji_latency_sample).
  - `order-2025-11-26-061-campaign2-telemetry.json` (latency/accuracy aggregates, guardrails, wheel layout).
- Metrics tracked: time_to_fun_ms, revive_ms, avg/p95 command latency, command_accuracy, one_more_accept, hud_signals counts.

Playtest loop (90s tutorial):
1) Wheel open -> shield ally (time_to_fun anchor).
2) Tempo forge, danger ping, dream drop, scout ping.
3) Guardrail rejection sample (unknown token) to prove DSL filter.
4) Downed -> revive ping -> revive cast (revive_ms), fallback signal.
5) Checkpoint + one-more-run prompt.

Next steps to wire real UI:
- Bind wheel slots to DSL ids above; call `CommandTelemetry.record_command` for every cast/ping and `record_ui_state/record_revive/record_one_more_prompt` for HUD signals.
- Use `CommandTelemetry.export_payloads` to feed UI logs or `write_outputs` to mirror to logs/ + attachments; emit `emoji_latency_sample` per command (latency from wheel open -> cast).
- Keep guardrails intact (no free text) and mirror telemetry to the hub alongside cadence/emitter smoke once a real playtest runs.
