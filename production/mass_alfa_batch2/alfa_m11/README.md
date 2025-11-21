# Alfa-M11 - Genesis Batch 2

- **Order**: `order-2025-11-19-060`
- **Baseline**: `forge-alfa@2025-11-19-060`
- **Path**: `production/mass_alfa_batch2/alfa_m11`
- **Exchange slot**: `genesis-iota`
- **Focus**: Layer-stacked cadence once cooldown stays under control.

Evidence checklist
- `logs/readiness.json` – Batch 2 readiness run (re-run after iota hydration to capture cooldown metrics).
- `logs/smoke.txt` – CLI smoke transcript stored for schema parity.

Next steps
1. Hydrate `golf_07/iota_05/alfa_m11` and wire cooldown telemetry hooks.
2. Re-run readiness + smoke with layered spans noted so Toyfoundry can trace cooldown performance.
3. File hello + telemetry delta referencing the layered cadence once the target workspace signs off.
