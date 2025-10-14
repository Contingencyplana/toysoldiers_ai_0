Toyfoundry import staging
=========================

Drop the Toyfoundry telemetry samples and schema here to enable
local ingestion and validation for order-2025-10-14-011.

Expected paths (relative to repo root):
- .imports/toyfoundry/telemetry/quilt/exports/samples/composite_export.sample.json
- .imports/toyfoundry/telemetry/quilt/exports/samples/composite_export.sample.csv
- .imports/toyfoundry/telemetry/quilt/exports/export_schema.md

Optional (if available):
- .imports/toyfoundry/telemetry/quilt/exports/build_info.json

Checksums to verify against (from exchange/reports/archived/order-2025-10-14-010-report.json):
- JSON sample SHA256: b9961c6c6f9f55120186ab1afb915b4e07fa4318f05a776158eef6f300261a52
- CSV sample SHA256:  e607bc75e0f0a3bc575bcfc2a1b4049e56374c5f0a23c830f30b1fce792b6616

After dropping files, run one of:
- PowerShell (recommended):
  powershell -ExecutionPolicy Bypass -File tools/consumer_ingest.ps1 `
    -JsonPath .imports/toyfoundry/telemetry/quilt/exports/samples/composite_export.sample.json `
    -CsvPath  .imports/toyfoundry/telemetry/quilt/exports/samples/composite_export.sample.csv `
    -SchemaPath .imports/toyfoundry/telemetry/quilt/exports/export_schema.md `
    -ReportPath exchange/reports/inbox/order-2025-10-14-011-report.json

- Python (if available):
  python -m tools.consumer_ingest \
    --json .imports/toyfoundry/telemetry/quilt/exports/samples/composite_export.sample.json \
    --csv  .imports/toyfoundry/telemetry/quilt/exports/samples/composite_export.sample.csv \
    --schema .imports/toyfoundry/telemetry/quilt/exports/export_schema.md \
    --report exchange/reports/inbox/order-2025-10-14-011-report.json
