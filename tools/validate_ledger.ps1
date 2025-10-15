param(
  [string]$LedgerPath = 'exchange/ledger/index.json',
  [switch]$CheckStaged
)

$ErrorActionPreference = 'Stop'

function Add-Err([string]$msg){
  [void]$script:Errors.Add($msg)
}

if (-not (Test-Path -LiteralPath $LedgerPath)) {
  Write-Error "Ledger not found: $LedgerPath"
  exit 2
}

$raw = Get-Content -Raw -LiteralPath $LedgerPath
$ledger = $raw | ConvertFrom-Json
$Errors = New-Object System.Collections.Generic.List[string]

# Validate acks map
foreach ($prop in ($ledger.acks.PSObject.Properties)) {
  $name = $prop.Name
  $path = Join-Path 'exchange' $prop.Value
  if (-not (Test-Path -LiteralPath $path)) {
    # Try to locate by filename anywhere under acknowledgements
    $fname = Split-Path -Leaf $path
    $alt = Get-ChildItem -Recurse -File -Path 'exchange/acknowledgements' -Filter $fname -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($alt) {
      Add-Err "ACK path mismatch for $name; ledger=$($prop.Value) actual=$($alt.FullName.Replace((Resolve-Path .).Path + '\\','exchange\\'))"
    } else {
      Add-Err "ACK missing for $name at $($prop.Value)"
    }
  }
}

# Validate reports map
foreach ($prop in ($ledger.reports.PSObject.Properties)) {
  $name = $prop.Name
  $path = Join-Path 'exchange' $prop.Value
  if (-not (Test-Path -LiteralPath $path)) {
    $fname = Split-Path -Leaf $path
    $alt = Get-ChildItem -Recurse -File -Path 'exchange/reports' -Filter $fname -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($alt) {
      Add-Err "Report path mismatch for $name; ledger=$($prop.Value) actual=$($alt.FullName.Replace((Resolve-Path .).Path + '\\','exchange\\'))"
    } else {
      Add-Err "Report missing for $name at $($prop.Value)"
    }
  }
}

# Cross-check orders entries
foreach ($oprop in ($ledger.orders.PSObject.Properties)) {
  $oid = $oprop.Name
  $order = $oprop.Value
  $ackKey = "$oid-ack"
  $repKey = "$oid-report"

  # Ack path should match acks map
  if ($ledger.acks.$ackKey) {
    if ($order.ack_path -ne $ledger.acks.$ackKey) {
      Add-Err "Order $oid ack_path mismatch; orders=$($order.ack_path) acks=$($ledger.acks.$ackKey)"
    }
  }

  # Report path should match reports map
  if ($ledger.reports.$repKey) {
    if ($order.report_path -ne $ledger.reports.$repKey) {
      Add-Err "Order $oid report_path mismatch; orders=$($order.report_path) reports=$($ledger.reports.$repKey)"
    }
  }

  # Location policy: closed -> archived; others -> inbox
  $repPath = $order.report_path
  if ($repPath) {
    if ($order.status -eq 'closed') {
      if (-not $repPath.StartsWith('reports/archived/')) {
        Add-Err "Order $oid is closed but report_path not archived: $repPath"
      }
    } else {
      if (-not $repPath.StartsWith('reports/inbox/')) {
        Add-Err "Order $oid is not closed but report_path not in inbox: $repPath"
      }
    }
  }
}

if ($Errors.Count -gt 0) {
  Write-Host "Ledger validation FAILED (" $Errors.Count ")" -ForegroundColor Red
  $Errors | ForEach-Object { Write-Host " - $_" }
  exit 1
}

# Optional staged-change guardrails (pre-commit)
if ($CheckStaged) {
  try {
    $staged = git diff --cached --name-status 2>$null
  } catch {
    Add-Err "Unable to read staged changes via git"
  }
  if ($staged) {
    $addedDispatched = New-Object System.Collections.Generic.HashSet[string]
    $deletedPending = New-Object System.Collections.Generic.HashSet[string]
    $renamedOk = New-Object System.Collections.Generic.HashSet[string]

    foreach ($line in ($staged -split "`n")) {
      $ln = $line.Trim()
      if (-not $ln) { continue }
      $parts = $ln -split "\s+"
      if ($parts[0] -like 'R*' -and $parts.Count -ge 3) {
        $old = $parts[1]; $new = $parts[2]
        if ($old -like 'exchange/orders/pending/*' -and $new -like 'exchange/orders/dispatched/*') {
          $renamedOk.Add([IO.Path]::GetFileName($new)) | Out-Null
        }
        continue
      }
      if ($parts.Count -ge 2) {
        $status = $parts[0]; $path = $parts[1]
        if ($status -eq 'A' -and $path -like 'exchange/orders/dispatched/*') {
          $addedDispatched.Add([IO.Path]::GetFileName($path)) | Out-Null
        }
        if ($status -eq 'D' -and $path -like 'exchange/orders/pending/*') {
          $deletedPending.Add([IO.Path]::GetFileName($path)) | Out-Null
        }
      }
    }

    foreach ($fname in $addedDispatched) {
      if (-not ($deletedPending.Contains($fname) -or $renamedOk.Contains($fname))) {
        # Check for existence in HEAD or working tree as pending (tolerate move not staged as rename)
        $pendingRel = "exchange/orders/pending/$fname"
        $existsWorking = Test-Path -LiteralPath $pendingRel
        $existsHead = $false
        try {
          $existsHead = [bool](git ls-tree -r --name-only HEAD -- "exchange/orders/pending/$fname" 2>$null)
        } catch { $existsHead = $false }
        if (-not ($existsWorking -or $existsHead)) {
          Add-Err "New dispatched order added without corresponding pending: $fname"
        }
      }
    }
  }
}

if ($Errors.Count -gt 0) {
  Write-Host "Ledger validation FAILED (" $Errors.Count ")" -ForegroundColor Red
  $Errors | ForEach-Object { Write-Host " - $_" }
  exit 1
}

Write-Host "Ledger validation OK" -ForegroundColor Green
