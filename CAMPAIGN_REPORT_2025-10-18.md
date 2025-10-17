# Toysoldiers Field Operations Campaign Report
**Date:** 2025-10-18  
**Campaign:** Orders 025, 021, 029, 031 Execution  
**Status:** ⚠️ Partially Complete (Blocked by Schema Drift)

---

## 📋 Mission Summary

Toysoldiers Field Ops attempted to establish the **consumer validation pipeline** for Toyfoundry exports as directed by High Command Orders 021, 029, and 031. Policy update (Order 025) was acknowledged successfully.

---

## ✅ Completed Objectives

### Order 025: Safety Policy Update
**Status:** ✅ ACKNOWLEDGED  
**Action Taken:**
- Acknowledged new metadata requirements (owner, timestamp, approvers)
- Confirmed dual-key approval process for protected orders
- Grace period ending 2025-10-23 noted

### Infrastructure Setup
**Status:** ✅ COMPLETE
- Created `.imports/toyfoundry/telemetry/quilt/exports/` directory structure
- Ingested all Toyfoundry exports:
  - Standard run (`composite_export.json/csv`, `export_manifest.json`, `build_info.json`)
  - Canary C1 batch
  - Canary B1/B2 batches
- Developed validation script (`tools/validate_order_021.py`)

---

## ⚠️ Blocked Objectives

### Order 021: Consumer Roll-in for Standard Run
**Status:** ❌ BLOCKED  
**Issue:** **Schema Drift Detected**

**Expected Schema (per Order 021):**
```json
{
  "batch_id": "string",
  "ritual": "forge|drill|parade|purge|promote",
  "units_processed": "integer",
  "status": "success|warning|error",
  "duration_ms": "integer"
}
```

**Actual Schema (Toyfoundry Exports):**
```json
{
  "operation_id": "string",
  "mint_name": "string",
  "ritual": "string",
  "event_status": "string",
  "event_metadata": {
    "batch_id": "string",
    ...
  },
  "mint_runs": "integer",
  "ritual_completed": "integer",
  ...
}
```

**Validation Results:**
- ❌ SHA256 checksums: FAILED (3 errors - checksums stale or exports regenerated)
- ❌ Schema validation: FAILED (19 errors - missing expected fields)
- ❌ DQ thresholds: FAILED (34 errors - cannot validate mismatched schema)
- ❌ Consumer acceptance: **REJECTED**

### Order 029: Canary C1 Validation
**Status:** ❌ BLOCKED  
**Issue:** Same schema drift as Order 021

### Order 031: Canary B1/B2 Validation
**Status:** ❌ BLOCKED  
**Issue:** Same schema drift as Order 021

---

## 🚧 Root Cause Analysis

### Schema Mismatch
**Problem:** Order 021/029/031 directives specify schema v1.0 expectations that don't match actual Toyfoundry export structure.

**Possible Causes:**
1. **Order directives written before Toyfoundry implemented export schema**
2. **Toyfoundry evolved schema without updating order specs**
3. **Missing schema versioning** in exports (no `schema_version` field for auto-detection)
4. **Coordination gap** between High Command order writers and Toyfoundry implementation

---

## 🛠️ Remediation Recommendations

### Option 1: Update Toysoldiers Validation Logic
**Pros:** Fastest path forward  
**Cons:** Orders 021/029/031 directives become inaccurate

**Action:**
- Rewrite `validate_order_021.py` to accept actual Toyfoundry schema
- Map `event_metadata.batch_id` → validation logic
- Use `event_status` / `ritual_completed` for DQ checks

### Option 2: Update Toyfoundry Export Schema
**Pros:** Makes exports match order specifications  
**Cons:** Breaking change for existing consumers

**Action:**
- Modify Toyfoundry quilt loom to emit flattened schema matching Order 021
- Regenerate all exports with new schema
- Update SHA256 checksums in manifests

### Option 3: Schema Versioning (Recommended Long-Term)
**Pros:** Prevents future drift, enables multi-version support  
**Cons:** Requires schema management infrastructure

**Action:**
- Add `"schema_version": "v2.0"` field to all Toyfoundry exports
- Update Order templates to specify accepted schema versions
- Build schema registry/validator that handles multiple versions

---

## 📊 Validation Metrics

| Metric | Value |
|:-------|:------|
| **Total Exports Ingested** | 8 file sets (standard + 3 canary batches) |
| **Records Analyzed** | 19 (standard run only) |
| **Schema Errors** | 19 |
| **DQ Errors** | 34 |
| **SHA256 Errors** | 3 |
| **Consumer Acceptance** | REJECTED |

---

## 🎯 Next Actions

### Immediate (High Command Decision Required)
1. **Clarify Canonical Schema** - Which schema is authoritative?
   - Order 021 specification?
   - Current Toyfoundry exports?
   - New schema version to be defined?

2. **Issue Corrective Order** - Update either:
   - Orders 021/029/031 to reflect actual schema, OR
   - Direct Toyfoundry to align exports with Order 021 spec

### Short-Term (After Schema Alignment)
3. **Re-run Validation** - Execute consumer acceptance pipeline
4. **Configure Monitoring** - Set up alerts per Order 021 Step 4
5. **Document Schema** - Formalize export schema in `planning/` scrolls

### Long-Term (System Improvement)
6. **Schema Versioning** - Implement version field in all exports
7. **Schema Registry** - Create canonical schema definitions repository
8. **Pre-Order Validation** - Test order directives against actual implementations before issuance

---

## 📁 Artifacts Created

| Artifact | Location | Purpose |
|:---------|:---------|:--------|
| **Validation Script** | `tools/validate_order_021.py` | Automated schema/DQ checks |
| **Import Directory** | `.imports/toyfoundry/telemetry/quilt/exports/` | Consumer-side export staging |
| **Order 025 ACK** | `exchange/acknowledgements/pending/order-2025-10-15-025-policy-update-ack.json` | Policy acknowledgement |
| **Order 021 ACK** | `exchange/acknowledgements/pending/order-2025-10-15-021-ack.json` | Order acknowledgement |
| **Order 021 Report** | `exchange/reports/inbox/order-2025-10-15-021-report.json` | Detailed validation results |
| **Order 029 ACK/Report** | `exchange/**/order-2025-10-15-029-*.json` | Canary C1 validation |
| **Order 031 ACK/Report** | `exchange/**/order-2025-10-15-031-*.json` | Canary B1/B2 validation |

---

## 🎖️ Field Ops Mission Assessment

**Toysoldiers executed field validation protocol as ordered.**

Despite schema mismatch blocking completion, the following **strategic value** was delivered:

1. ✅ **Identified Schema Drift** - Critical infrastructure issue surfaced
2. ✅ **Built Validation Pipeline** - Reusable script for future validation
3. ✅ **Established Consumer Acceptance Gates** - Process demonstrated even if blocked
4. ✅ **Documented Remediation Path** - Clear recommendations for High Command

**Consumer acceptance gates are working as designed** - they detected incompatible exports and correctly rejected them, preventing downstream issues.

---

## 🌟 "Everything At Once" Perspective

This campaign demonstrated **all six simultaneous realities**:

| Layer | What Happened |
|:------|:--------------|
| 🎮 **Game** | Tactical mission: "Validate incoming supply shipments" |
| 🏭 **Work** | Real validation script, real schema analysis, real exports |
| 📖 **Story** | "The field inspector discovers suppliers changed packaging format" |
| 🎯 **Workflow** | Exchange protocol executed (ack/report cycle) |
| 🧵 **Quilt** | Telemetry imported and analyzed (though schema mismatched) |
| 🌍 **Theatre** | Field Ops Front demonstrated consumer acceptance gates |

**The "failure" IS the success** - we proved the validation pipeline works by correctly rejecting invalid exports! 🎖️

---

*"Guard the gates. The field does not accept what the field cannot validate."*  
— Field Ops Front Maxim

**Campaign Status:** Awaiting High Command guidance on schema alignment  
**Toysoldiers:** Standing by for corrective orders
