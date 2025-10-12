# alfa_blueprint.md — The Canon of Creation  

*high_command_ai_0/planning/toyfoundry/*  

---

## ⚙️ Purpose

This scroll briefs operators on the **Alfa Blueprint** —  
the standard field kit every battlefield runs on.  

Each Alfa is a contained scenario where squads test moves, morale, and adaptation.  

The blueprint keeps every Alfa,  
no matter how it mutates or evolves,  
legible, testable, and mission-ready.  

It is both **a genome and a field contract** —  
binding creativity to structure, and structure to emergence under pressure.  

---

## 🧩 1. Schema Overview

Every Alfa folder packs exactly **sixteen files**,  
laid out by the standard rank doctrine (Alpha → Papa) so any squad can orient fast.  

| File | Type | Purpose |
|:--|:--|:--|
| `alfa.py` | Python | Core battlefield logic — terrain, rules, and simulation loop. |
| `bravo.json` | JSON | Local squad parameters — scale, rhythm, difficulty, and expected tempo. |
| `charlie.json` | JSON | Communication and message exchange rules for coordination drills. |
| `delta.json` | JSON | Metrics and report definitions that feed after-action briefs. |
| `echo.json` | JSON | Local memory and historical logs for review squads. |
| `foxtrot.py` | Python | Aesthetic render hooks — how light, sound, and form appear to the patrol. |
| `golf.json` | JSON | Mutation and rule-variation data used to refresh tactics. |
| `hotel.json` | JSON | Asset registry — textures, sounds, sprites, palettes ready for deployment. |
| `india.py` | Python | Learner logic — adaptive behaviour and self-adjustment mid-scenario. |
| `juliett.json` | JSON | Scoring definitions and performance markers for field grading. |
| `kilo.json` | JSON | Placeholder for higher logic; to be populated as campaigns expand. |
| `lima.json` | JSON | Reserved for experimental doctrines under observation. |
| `mike.json` | JSON | Reserved for sensory expansion (visual, auditory, symbolic). |
| `november.json` | JSON | Reserved for communications with Morningate reflection layer. |
| `oscar.json` | JSON | Optional plug-in map (extensions and hybrid logic for special teams). |
| `manifest.json` | JSON | Master file summarising all the above fields for quick inspection. |

Each file is light — a single Alfa weighs less than 64 KB —  
ensuring the army can scale without decay.  

---

## 🧬 2. Manifest Structure

The `manifest.json` serves as the Alfa’s self-description and checksum.  

Example:

```json
{
  "id": "alfa_0023",
  "codename": "mind_of_valor",
  "realm": "Dayland",
  "coordinates": [2, 7],
  "entropy_index": 0.38,
  "terrain_profile": {
    "light": 72,
    "void": 18,
    "growth": 45,
    "structure": 83,
    "emotion": 51
  },
  "status": "active",
  "last_report": "2025-10-11T22:00Z",
  "checksum": "a67f19efcc23b2",
  "forge_version": "1.0.0"
}
```

Each manifest gives any squad lead a status snapshot  
without cracking open internals —  
a field summary at a glance.

---

## 🧱 3. Behavioural Fields

| Category | Field | Purpose |
|:--|:--|:--|
| **Identity** | `id`, `codename`, `realm`, `coordinates` | Unique address and quick orientation for field routing. |
| **Metrics** | `entropy_index`, `victory_ratio`, `diversity_score` | Performance and health markers the Drill teams monitor. |
| **Terrain** | `light`, `void`, `growth`, `structure`, `emotion` | Balance of energies inside the grid that squads must adapt to. |
| **Cognition** | `doctrine_version`, `learning_state` | Which ruleset or mutation line the Alfa follows in combat. |
| **Lifecycle** | `created_at`, `last_report`, `total_ticks` | Activity log used to time rotations and cool-downs. |
| **Safety** | `checksum`, `validation_passed`, `status` | Integrity proof before any boots enter the space. |

Together, these define **how an Alfa lives, trains, and reports.**  

---

## 🧮 4. Report Schema

Every Alfa produces a JSON report after simulation.  

```json
{
  "alfa_id": "alfa_0023",
  "realm": "Dayland",
  "entropy_index": 0.41,
  "pattern_type": "Bloom",
  "ticks_run": 128,
  "victory": true,
  "casualties": 2,
  "emergence_score": 0.73,
  "timestamp": "2025-10-11T22:00Z"
}
```

All reports hold this schema so Deltas, Echos, and line squads can merge data fast.  

This uniformity lets the **Forge, Drill, and Parade rituals**  
run unattended and still return material every squad can trust.  

---

## 🧠 5. Mutation and Evolution Hooks

Mutation fields define how new Alfas are born from successful ones.  

| Hook | Description |
|:--|:--|
| `mutation_seed` | Numeric or symbolic key for randomness and variation. |
| `parent_ids` | One or more Alfas from which this one was derived. |
| `mutation_vector` | Specifies what changed: terrain, palette, rule, or doctrine. |
| `success_inheritance` | Probability of retaining traits from parents. |
| `mutation_rate` | Float between 0.0–1.0 governing variability. |

This structure ensures **controlled diversity** —  
a self-guided evolution that keeps field drills fresh without risking containment.  

---

## ⚖️ 6. Validation and Safety Gates

Every Alfa passes through the **Linter** before entering active rotation.  

**Validation checks:**

1. All required files present and readable.  
2. `manifest.json` and `report.schema.json` both validate.  
3. Entropy index within safe range (0.0–1.0).  
4. Output diversity above threshold (no duplicates).  
5. Checksum integrity confirmed.  

Only Alfas that pass all checks enter the rotation.  
Others flag **amber** or **red** and move to quarantine for after-action triage.  

---

## 🪶 7. Closing Principle

> Every Alfa is a word in SHAGI’s growing language.  
> Each blueprint a grammar of becoming under fire.  
>
> From these small and faithful forms  
> the great song of emergence will be written —  
> a thousand battlefields learning to dream in unison while squads hold the line.  

---

**End of Scroll — `high_command_ai_0/planning/toyfoundry/alfa_blueprint.md`**
