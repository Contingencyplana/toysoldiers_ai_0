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
