Lightweight Monitoring for Ingestion & Schema Drift

Signals
- ingestion_failure: Non-zero exit from ingestion/validation scripts, or report.acceptance.status == "blocked".
- schema_drift: schema_validation.unexpected_fields or field_mismatches not empty, or confirmed_version != expected_version.

Scripts
- One-shot wrapper: `pwsh ./tools/validate_exports.ps1` (exits non-zero on failure)
- Ingestion: `python -m tools.consumer_ingest --json <json> --csv <csv> --schema <schema_md> --report <report.json>`
- Validation: `python -m tools.consumer_validate --report <report.json>`

Exit Codes
- 0: Ingestion and validation succeeded; report.status is "ready_for_review".
- 1: Ingestion or validation blocked; see report.acceptance.blockers.

Remediation
- Check source paths exist and are readable.
- Reconcile field set with schema (EXPECTED_FIELDS in validator) if Toyfoundry updates exports.
- Investigate out-of-range durations or non-positive units; correct upstream or document exceptions as constraints.

Automation Tip (PowerShell)
```
python -m tools.consumer_ingest `
  --json .imports/toyfoundry/telemetry/quilt/exports/samples/composite_export.sample.json `
  --csv  .imports/toyfoundry/telemetry/quilt/exports/samples/composite_export.sample.csv `
  --schema .imports/toyfoundry/telemetry/quilt/exports/export_schema.md `
  --report exchange/reports/inbox/order-2025-10-14-013-report.json

python -m tools.consumer_validate `
  --report exchange/reports/inbox/order-2025-10-14-013-report.json

$report = Get-Content exchange/reports/inbox/order-2025-10-14-013-report.json -Raw | ConvertFrom-Json
if ($report.acceptance.status -ne 'accepted') { exit 1 }
exit 0
```

CI
- GitHub Actions workflow: `.github/workflows/validate_exports.yml` runs the wrapper on push/PR.
