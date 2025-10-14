# Toyfoundry Composite Telemetry Export Schema — v1.0

**Schema ID:** `toyfoundry-composite-telemetry@1.0`  
**Exported By:** Toyfoundry AI 0  
**Generated:** 2025-10-15  

---

## Overview
This schema describes unified telemetry exports produced by the Toyfoundry composite quilt loom.  
Each export represents a roll-up of multiple ritual streams: **Drill**, **Parade**, **Purge**, and **Promote**.

---

## JSON Structure

| Field | Type | Description |
|-------|------|-------------|
| `schema` | string | Identifier of the schema version. |
| `generated_at` | string (ISO8601) | Timestamp when the export was created. |
| `factory_id` | string | Name or code of the originating factory. |
| `batches` | array | List of ritual batch records. |
| `batches[].batch_id` | string | Unique batch identifier. |
| `batches[].ritual` | string | Ritual type (drill, parade, purge, promote). |
| `batches[].units_processed` | integer | Number of units processed in that ritual. |
| `batches[].status` | string | Status indicator (success, warning, failure). |
| `batches[].duration_ms` | integer | Time taken for the ritual batch in milliseconds. |
| `totals.rituals_logged` | integer | Number of rituals recorded. |
| `totals.units_processed` | integer | Total processed units. |
| `totals.average_duration_ms` | integer | Average ritual duration in milliseconds. |

---

## CSV Format
Identical semantics in flat table form:  
`batch_id,ritual,units_processed,status,duration_ms`

---

## Notes
- Intended consumers: **toysoldiers_ai_0** and related downstream analytics.  
- File integrity verified by SHA256 checks before ingestion.  
- All timestamps in UTC.

---
_Last updated: 2025-10-15_
