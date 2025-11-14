param(
  [string]$Report = "exchange/reports/inbox/order-2025-10-14-013-report.json",
  [string]$Json = ".imports/toyfoundry/telemetry/quilt/exports/samples/composite_export.sample.json",
  [string]$Csv = ".imports/toyfoundry/telemetry/quilt/exports/samples/composite_export.sample.csv",
  [string]$Schema = ".imports/toyfoundry/telemetry/quilt/exports/export_schema.md",
  [switch]$Quiet
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Note($msg) { if (-not $Quiet) { Write-Host $msg } }

$reportPath = Resolve-Path -LiteralPath (Split-Path -Path $Report -Parent) -ErrorAction SilentlyContinue
if (-not $reportPath) {
  $parent = Split-Path -Path $Report -Parent
  if ($parent) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
}

if (-not (Test-Path -LiteralPath $Report)) {
  Write-Note "[validate] Seeding missing report stub -> $Report"
  $reportId = [System.IO.Path]::GetFileNameWithoutExtension($Report)
  $relatesTo = $reportId -replace '-report$', ''
  $stub = @{
    schema = "field-report@1.0"
    report_id = $reportId
    relates_to = $relatesTo
    origin = "toysoldiers_ai_0"
    receiver = "high_command_ai_0"
    timestamp_sent = "<pending>"
    status = "pending"
    summary = "Automated placeholder for Validate Exports workflow."
    sources = @{
      sample_json = $Json
      sample_csv = $Csv
      export_schema_path = $Schema
    }
    ingestion_log = @{
      records_total = $null
      parse_errors = @()
      notes = @()
    }
    schema_validation = @{
      expected_version = "v1.0"
      confirmed_version = $null
      field_mismatches = @()
      unexpected_fields = @()
    }
    acceptance = @{
      status = "pending"
      constraints = @()
      blockers = @()
    }
  }
  $stub | ConvertTo-Json -Depth 6 | Out-File -FilePath $Report -Encoding utf8
}

Write-Note "[validate] Ingesting artifacts -> $Report"
python -m tools.consumer_ingest --json $Json --csv $Csv --schema $Schema --report $Report

Write-Note "[validate] Running validation + DQ checks"
python -m tools.consumer_validate --report $Report

$reportMap = Get-Content -LiteralPath $Report -Raw -Encoding UTF8 | ConvertFrom-Json -AsHashtable

$status = $null
if ($reportMap.ContainsKey('status')) { $status = $reportMap['status'] }

$acc = $null
$blockers = @()
if ($reportMap.ContainsKey('acceptance')) {
  $accObj = $reportMap['acceptance']
  if ($accObj -and $accObj.ContainsKey('status')) { $acc = $accObj['status'] }
  if ($accObj -and $accObj.ContainsKey('blockers') -and $accObj['blockers']) { $blockers = $accObj['blockers'] }
}

# Collect DQ failures for messaging
$dqFailed = @()
if ($reportMap.ContainsKey('dq_checks') -and $reportMap['dq_checks']) {
  $dq = $reportMap['dq_checks']
  foreach ($k in $dq.Keys) {
    $entry = $dq[$k]
    if ($null -ne $entry -and -not $entry.passed) { $dqFailed += $k }
  }
}

$unexpectedFields = @()
$missingFields = @()
if ($reportMap.ContainsKey('schema_validation') -and $reportMap['schema_validation']) {
  $sv = $reportMap['schema_validation']
  if ($sv.ContainsKey('unexpected_fields') -and $sv['unexpected_fields']) { $unexpectedFields = $sv['unexpected_fields'] }
  if ($sv.ContainsKey('field_mismatches') -and $sv['field_mismatches']) { $missingFields = $sv['field_mismatches'] }
}

if ($acc -ne 'accepted' -or $status -ne 'ready_for_review') {
  Write-Error ("Validation failed. acceptance={0}, status={1}" -f $acc, $status)
  if ($blockers.Count -gt 0) { Write-Host "Blockers:" ($blockers -join '; ') }
  if ($dqFailed.Count -gt 0) { Write-Host "DQ failed:" ($dqFailed -join ', ') }
  if ($unexpectedFields.Count -gt 0) { Write-Host "Unexpected fields:" ($unexpectedFields -join ', ') }
  if ($missingFields.Count -gt 0) { Write-Host "Missing fields:" ($missingFields -join ', ') }
  exit 1
}

$recordsTotal = $null
if ($reportMap.ContainsKey('ingestion_log') -and $reportMap['ingestion_log'] -and $reportMap['ingestion_log'].ContainsKey('records_total')) { $recordsTotal = $reportMap['ingestion_log']['records_total'] }
Write-Note ("[validate] OK: records_total={0}, acceptance=accepted" -f $recordsTotal)
exit 0
