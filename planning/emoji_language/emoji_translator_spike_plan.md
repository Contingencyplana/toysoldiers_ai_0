# Emoji Translator & Narration Spike Plan

**Author:** toysoldiers_ai_0
**Date:** 2025-10-25
**Status:** Draft (pending High Command review)

---

## 1. Mission Objective

Prototype an emoji-first command pipeline that proves the viability of Major Pivot Five inside the Toysoldiers/Toyfoundry runtime. The spike provides a reversible sandbox implementation that:

- Accepts glyph chains from operators (human or AI) without requiring textual commands.
- Compiles glyph chains into the existing exchange order payloads used by Toyfoundry and Toysoldiers.
- Plays synchronized narration so pre-literate players get audible confirmation alongside visual feedback.
- Surfaces validation hooks so Order 021–style checks can extend to emoji programs.

The spike produces decision data and scaffolding; it is not intended for production deployment without follow-up hardening.

---

## 2. Current Runtime Touchpoints

| Surface | File(s) / Location | Notes |
|---------|--------------------|-------|
| Toysoldiers command intake | `tools/consumer_ingest.py`, `tools/validate_order_021.py`, `.imports/` staging tree | Current flow expects JSON/CSV exports produced by Toyfoundry and referenced in exchange orders. |
| Toyfoundry emission | `.toyfoundry/telemetry/quilt/exports/**` | Emits composite telemetry artifacts with manifests and checksums. |
| Exchange protocol | `exchange/orders/**`, `exchange/reports/**` | JSON directives and reports remain the source of truth for High Command tasks. |

The spike must interpose above the existing JSON layer so emoji commands can be transformed before hitting the established validation and reporting steps.

---

## 3. Spike Scope

1. **Glyph Intake Module**
   - Accepts an ordered list of glyph identifiers (e.g., `['forge', 'craft', 'ally', 'victory']`).
   - Validates glyphs against the Level-0 lexicon (32 symbols defined in `new_major_pivots/new_major_pivot_5.md`).

2. **Translator Bridge**
   - Maps glyph sequences to structured intent (target Alfa, ritual, payload parameters).
   - Emits provisional JSON payload matching current exchange order schema (factory-order@1.0, factory-report@1.0).
   - Logs round-trip data for inspection (glyph chain → JSON → glyph chain).

3. **Narration Layer**
   - Selects pre-scripted narration lines per glyph chain (stubbed TTS call or audio-file reference).
   - Provides synchronous playback hook (no audio assets required for spike; textual stub acceptable).

4. **Validation Hook**
   - Invokes existing `validate_order_021.py` with generated payloads where applicable.
   - Records validation outcome alongside glyph metadata for later analytics.

Out of scope: production audio asset pipeline, accessibility QA, multiplayer synchronization.

---

## 4. Deliverables

| Artifact | Description |
|----------|-------------|
| `planning/emoji_language/translator_spike_design.md` (this doc evolves) | Finalized plan + outcomes. |
| Prototype Python module (likely under `tools/emoji_translator_spike.py`) | Implements glyph intake, translation, narration stubs, validation bridge. |
| Sample glyph scripts (`samples/emoji_commands/*.json`) | Demonstrate Level-0 command coverage. |
| Spike report | Summarizes findings, gaps, and recommendations before productionizing. |

---

## 5. Dependencies & Inputs

- **Glyph Lexicon:** Defined in `new_major_pivot_5.md`; may need to replicate as machine-readable data (JSON map or Python dict).
- **Narration Script:** Requires draft copy text per glyph and per composite program; coordinate with War Office lore team once spike proves value.
- **Audio Engine:** For spike, use placeholder stub; future integration may target existing TTS service or new pipeline.
- **Toyfoundry Coordination:** Ensure translator output matches Toyfoundry’s expected order/ritual schema; schedule review with Toyfoundry_ai_0 prior to hardening.

---

## 6. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Translation ambiguity (multiple glyph combos map to same command) | Confusion, inconsistent automation | Maintain deterministic grammar and document invalid permutations during spike. |
| Narration drift from lore tone | Breaks immersion for toddlers/players | Work with lore team on vocabulary; keep stub script editable. |
| Validation gaps for emoji payloads | Reintroduces schema drift | Extend existing validator once spike proves translation path; include checksum/hash recording. |
| Scope creep into productionization | Delays other fronts | Time-box spike, capture follow-up tasks separately. |

---

## 7. Spike Timeline (Draft)

| Phase | Duration | Exit Criteria |
|-------|----------|---------------|
| Planning & Alignment | 0.5 day | High Command approves scope and dependencies. |
| Translator Prototype | 1 day | Glyph chain converts to JSON order payloads; round-trip logged. |
| Narration Stub | 0.5 day | Glyph execution prints or queues narration lines. |
| Validation Hook | 0.5 day | Generated payload validated via `validate_order_021.py`; results recorded. |
| Synthesis Report | 0.5 day | Spike findings documented with go/no-go recommendations. |

Total estimated spike effort: **~3 days** (calendar flexible pending cross-team coordination).

---

## 8. Open Questions

1. Should the translator live in Toysoldiers runtime, Toyfoundry runtime, or as a shared service? (Spike assumes local module for experimentation.)
2. What persistence format will store glyph sessions for replay? (JSON log vs. database.)
3. How should narration integrate with existing telemetry/quilt reporting? (Potential new event type.)
4. Which team owns long-term stewardship of the glyph lexicon and compiler rules?

---

*Prepared for review by High Command and Toyfoundry leadership. Awaiting approval before implementation begins.*
