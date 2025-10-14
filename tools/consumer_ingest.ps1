param(
  [Parameter(Mandatory=$true)] [string]$ReportPath,
  [Parameter(Mandatory=$false)] [string]$JsonPath,
  [Parameter(Mandatory=$false)] [string]$CsvPath,
  [Parameter(Mandatory=$false)] [string]$SchemaPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-Sha256($Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return $null }
  try { (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLower() } catch { $null }
}

function Get-JsonRecords($Path) {
  if (-not (Test-Path -LiteralPath $Path)) { throw "JSON not found: $Path" }
  $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($raw -is [System.Collections.IEnumerable] -and -not ($raw -is [string])) { return ,$raw }
  foreach ($key in @('records','items','data','batches')) {
    if ($null -ne ($raw.PSObject.Properties.Item($key))) {
      $val = $raw.$key
      if ($val -is [System.Collections.IEnumerable] -and -not ($val -is [string])) { return ,$val }
    }
  }
  throw "Unsupported JSON structure (expected array or object with records/items/data/batches)"
}

function Get-FieldUnion($Records) {
  $set = @{}
  foreach ($rec in $Records) {
    foreach ($n in $rec.PSObject.Properties.Name) { $set[$n] = $true }
  }
  return ($set.Keys | Sort-Object)
}

function Get-SchemaVersion($SchemaPath) {
  if (-not $SchemaPath -or -not (Test-Path -LiteralPath $SchemaPath)) { return $null }
  $text = Get-Content -LiteralPath $SchemaPath -Raw -Encoding UTF8
  $lines = $text -split "`n"
  $m = ($lines | Select-String -Pattern 'v\d+\.\d+' -SimpleMatch:$false -AllMatches | Select-Object -First 1)
  if ($m -and $m.Matches.Count -gt 0) { return $m.Matches[0].Value }
  $m2 = Select-String -InputObject $text -Pattern '(?im)Schema ID:\s*[^@]+@(\d+\.\d+)' | Select-Object -First 1
  if ($m2 -and $m2.Matches.Count -gt 0) { return "v" + $m2.Matches[0].Groups[1].Value }
  return $null
}

if (-not (Test-Path -LiteralPath $ReportPath)) { throw "Report JSON not found: $ReportPath" }
$report = Get-Content -LiteralPath $ReportPath -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $report.ingestion_log) { $report | Add-Member -NotePropertyName ingestion_log -NotePropertyValue (@{}) }
if (-not $report.schema_validation) { $report | Add-Member -NotePropertyName schema_validation -NotePropertyValue (@{}) }
if (-not $report.acceptance) { $report | Add-Member -NotePropertyName acceptance -NotePropertyValue (@{}) }

$parseErrors = @()

if ($CsvPath) {
  try {
    $rows = Import-Csv -LiteralPath $CsvPath
    $fields = @()
    if ($rows.Count -gt 0) { $fields = ($rows[0].PSObject.Properties.Name | Sort-Object) }
    $report.ingestion_log.csv = [ordered]@{
      path = $CsvPath
      records = [int]$rows.Count
      fields = $fields
      sha256 = (Get-Sha256 -Path $CsvPath)
    }
  } catch {
    $parseErrors += "CSV: $($_.Exception.Message)"
  }
}

if ($JsonPath) {
  try {
    $records = Get-JsonRecords -Path $JsonPath
    $fields = Get-FieldUnion -Records $records
    $report.ingestion_log.json = [ordered]@{
      path = $JsonPath
      records = [int]$records.Count
      fields = $fields
      sha256 = (Get-Sha256 -Path $JsonPath)
    }
  } catch {
    $parseErrors += "JSON: $($_.Exception.Message)"
  }
}

$total = 0
foreach ($k in @('csv','json')) { if ($report.ingestion_log.$k -and $report.ingestion_log.$k.records) { $total += [int]$report.ingestion_log.$k.records } }
$report.ingestion_log.records_total = if ($total -gt 0) { $total } else { $null }

$confirmed = Get-SchemaVersion -SchemaPath $SchemaPath
if ($confirmed) { $report.schema_validation.confirmed_version = $confirmed }

if ($parseErrors.Count -gt 0) {
  $report.acceptance.status = 'blocked'
  $report.acceptance.blockers = $parseErrors
} else {
  if (-not $report.acceptance.status) { $report.acceptance.status = 'pending' }
}

$report | ConvertTo-Json -Depth 16 | Set-Content -LiteralPath $ReportPath -Encoding UTF8
Write-Host "Updated report:" $ReportPath

