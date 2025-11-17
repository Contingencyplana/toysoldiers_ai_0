# Toysoldiers Field Operations RUNBOOK

> Execute with precision, powered by intelligence.

## Scope & Intent
- Maintains tactical readiness for the Field Operations Front so orders, acknowledgements, and reports clear the exchange without blockers.
- Tracks the flow from 16x16 emoji battlegrids, through the golf theaters, into the Toyfoundry exchange hub (`C:\Users\Admin\high_command_exchange`).
- Governs readiness for missions tied to Major Pivot Five (emoji-first command surface) and routine Alfa deployments.

## Contacts & Escalation
| Role | Owner | How to page |
| --- | --- | --- |
| Primary Field Ops On-Call | Echo (Ops Marshal) | Post in `#shagi-field-ops` and tag @echo |
| Secondary | Foxtrot (Bridge Liaison) | Direct DM plus `/incident start toysoldiers` |
| High Command Duty Officer | Rotation | `python tools/ping_high_command.py --workspace toysoldiers_ai_0` |

Escalation ladder: Primary -> Secondary -> Duty Officer -> Toyfoundry Flight (only if exchange is blocked for more than 30 minutes).

## Golden Signals
- `python -m tools.ops_readiness` returns `"ok": true`.
- `logs/exchange_all.json` shows the latest order/ack/report bundle with current UTC timestamp.
- `outbox/orders`, `outbox/acks`, and `outbox/reports` only contain staged files referenced in the latest Alfa mission (no file older than 48h).
- Emoji-first coverage: each outgoing order carries `payload.emoji_script_id` and round-trips cleanly through the narration layer.

## Daily Cadence
1. **Grid warm-up (T-60 minutes)**
   - If the Labscapes pool was powered down, run `python tools/labscape_control.py --scope golf --action warm_start`.
   - Review `planning/` updates and theater advisories.
2. **Readiness gate (T-30 minutes)**
   - Run `python -m tools.ops_readiness`.
   - If `docs_present` flags this runbook, restore it from git history or copy the latest approved text from High Command.
3. **Mission sync (T-15 minutes)**
   - `python tools/exchange_all.py --dry-run` (schema and emoji round-trip validation).
   - Confirm narration assets referenced in `exchange/audio/` exist when mission payloads include `narration_tracks`.
4. **Go/No-Go (T-0)**
   - Announce status in `#shagi-field-ops` with the readiness timestamp and `git rev-parse HEAD` hash.

## Daily Doc Refresh

Run this ritual the first time you touch Toysoldiers each day:

1. Run `python -m tools.ops_readiness`; if it fails, stop and fix readiness before editing.
2. Review `planning/commonwealth_loop/doc_refresh_queue.md` and select the highest-signal docs that need updates.
3. Refresh the selected scrolls (README, RUNBOOK, pivotal fronts, exchange guides) so they match current orders and telemetry evidence.
4. Log the refresh in both `exchange/ledger/2025-11.md` and `C:/Users/Admin/high_command_exchange/ledger/2025-11.md` with timestamp + scope.
5. Capture gaps or cross-workspace needs back into the queue and ping High Command when outside help is required.

Document each run by appending to the queue file so the ledger trail and checklist stay synced.

## Mitigation Playbooks
### Dual-layer cooldown blitz
- Source material: `exchange/reports/inbox/frontline_feedback_20251111T065332Z_genesis-delta.json` and `exchange/reports/inbox/frontline_feedback_20251111T072050Z_genesis-theta.json`.
- Assemble attendees: genesis-delta ops lead, genesis-theta ops lead, ritual queue owners, and the Toysoldiers duty officer.
1. Plot cooldown spikes by 15-minute windows using telemetry from the above reports plus live queue metrics.
2. Decide on mitigation:
   - **Parallelize rituals** if CPU/memory headroom exists; split the queue into paired lanes.
   - **Stagger rituals** if capacity is fixed; inject a 90-second offset for theta, then back off delta in 30-second increments until spikes normalize.
3. Document the chosen mitigation in the ops scratchpad, then update this runbook checklist before leaving the meeting.
4. Verification checklist:
   - [x] Queue change merged/configured in infrastructure repo (parallel lanes deployed 2025-11-13T16:10Z).
   - [x] Ritual owners sign off in `#shagi-field-ops`.
   - [x] Fresh delta/theta frontline feedback captured (see `frontline_feedback_20251113T171402Z_genesis-delta.json` and `frontline_feedback_20251113T171415Z_genesis-theta.json`).

### Zeta night-drill music patch
- Source material: `exchange/reports/inbox/frontline_feedback_20251111T072102Z_genesis-zeta.json`.
1. Pair the music lead (op-music-09) with the genesis-zeta operator during the next night drill rehearsal.
2. Capture exact clash cases by exporting the ritual timing stems and the night-drill preset mix.
3. Choose the fix:
   - Retune the preset to sit outside the ritual cue bands, **or**
   - Provide the fallback "ritual-safe" mix that locks to the metronome cues.
4. Validate with a full night-drill run; no cue drift or narration overlap is allowed.
5. Log the outcome with `python -m tools.frontline_feedback --workspace genesis-zeta` (include experience rating and note) and refresh the fleet summary via `python -m tools.frontline_feedback_summary`.
6. Post the new report links in `#shagi-field-ops` so High Command can reference the sentiment bump.

## Exchange Procedure
1. Run `python -m tools.ops_readiness`; do not proceed if `ok` is false.
2. Run `python tools/exchange_all.py` to validate JSON packages and mirror them into the hub.
3. Compare `logs/exchange_all.json` with the hub copy inside `high_command_ai_0/logs/exchange_all.json`. Filenames, sizes, and timestamps should match.
4. Post "Alfa package ready" with the file list, readiness time, and any special instructions (emoji translation IDs, narration notes, etc.).

### When exchange fails
- **Schema errors**: run `python tools/validate_payload.py <file>` and repair the JSON. Use `template/emoji_payload_example.json` as reference.
- **Hub offline**: keep files staged locally, open `/incident start toysoldiers hub-down`, and notify the Duty Officer.
- **Log written to wrong workspace**: inspect `tools/exchange_all.py` and ensure `LOG_ROOT = Path.cwd() / "logs"`. Update if necessary, rerun, and capture fresh logs.

## Incident Playbooks
### Readiness blocked by documentation
1. Verify `RUNBOOK.md` exists (this file) and contains the latest instructions.
2. Re-run readiness; attach the failing log lines to the incident if the gate stays red.

### Missing `created_at` in a report
1. Run `python tools/fix_report_timestamp.py --file <report>` or manually add an ISO-8601 UTC string under `metadata.created_at`.
2. Re-run readiness and exchange; ensure the corrected report propagates to the hub.

### Emoji narration drift
1. Compare `exchange/narration/*.json` to `tools/emoji_translator/config.json`.
2. If IDs differ, run `python tools/emoji_translator.py --sync narration` and revalidate orders referencing narration tracks.

### Golf theater outage
1. Identify the impacted theater (`golf_00` through `golf_15`).
2. Move workload via `python tools/theater_router.py --from golf_0X --to golf_0Y --reason <text>`.
3. Update `planning/theater_status.md` and notify the on-call.

## Verification Checklist (pre-commit)
- [ ] `python -m tools.ops_readiness`
- [ ] `python tools/exchange_all.py`
- [ ] `git status` shows only intentional changes
- [ ] `logs/ops_readiness.json` and `logs/exchange_all.json` timestamps are from the current session

## Reference Paths
- Orders: `exchange/orders/` (draft) -> `outbox/orders/` (staged) -> hub mirror.
- Acknowledgements: `outbox/acks/`
- Reports: `outbox/reports/`
- Logs: `logs/`
- Tooling: `tools/`

Maintain this runbook as tactics evolve. Every edit requires the duty officer sign-off plus a fresh readiness run.

