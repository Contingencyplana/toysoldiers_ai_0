# 🧪 ingredients_and_recipes.md — Atoms and Procedures

## 1. Ingredient categories

- **Symbols**: emoji/rune palette (🌕, 🕳️, 🌿, ⚙️, 🜛, 🔺, 💧, 🪶) — `field_lexicon.json`; tells squads which terrain mood they are stepping into.
- **Palettes**: color + lighting presets — `palettes/*.json`; sets tempo lighting for briefings and engagements.
- **SFX / Music**: short clips and mood loops — `soundbank/`; anchors trust-building rhythms between pushes.
- **Templates**:
  - `alfa_template/` (alfa.py + alfa.json baseline) for spinning up fresh ground fast.
  - `warroom_template/` for command cadence.
  - `wit_template/` to deploy thinking partners on demand.
- **Archetypes**: Toysoldier / Wit base configs (Scout, Builder, Healer, Wanderer; Analyst, Doubter, Optimist, Synthesist) — mix-and-match teams for balance across terrain types.
- **Rule snippets**: movement, diffusion, mutation modules — `rules/*.py`; swap to modulate tempo mid-mission.
- **Manifest schemas**: `manifest.schema.json` and `report.schema.json`; keep trust in the data loop tight.

## 2. Recipe categories

- **Forge:mint_alfa** — stand up fresh terrain with coordinates and manifest before squads arrive.
- **Run:simulate_alfa** — stress-test the ground for N ticks and ship `battle_report.json` to ops.
- **Report:aggregate** — roll child reports into `bravo_report.json` so tempo planning stays ahead.
- **Repair:quarantine_and_repair** — pull Nightland Alfas off the line, patch morale, redeploy.
- **Evolve:mutate_rules** — tweak `golf.json` rules, trial, and lock if the field likes the flow.
- **Dispatch:send_wit** — serialize a Wit and open a mindlink corridor between Alfas for shared trust.

## 3. Recipe schema (YAML example)

```yaml
# recipes/mint_alfa.yml
name: mint_alfa
version: 1.0
inputs:
  template: "templates/alfa_template"
  coords: [x, y]
  workspace: "making_friends_0"
outputs:
  - path: "alfas/alfa_{id}/"
steps:
  - copy: "{{inputs.template}} -> {{outputs[0]}}"
  - render: "{{outputs[0]}}/alfa.json" with:
      id: "alfa_{id}"
      coords: "{{inputs.coords}}"
      manifest.version: "{{name}}-{{version}}"
  - register: "manifests/alfas_index.json" append "{{outputs[0]}}/manifest.json"
checks:
  - exists: "{{outputs[0]}}/alfa.py"
  - json_valid: "{{outputs[0]}}/manifest.json" schema: "manifest.schema.json"
```

### 4. Starter Recipes (Short)

- **`mint_alfa`** → produces a playable Alfa ready for squad imprinting.  
- **`simulate_alfa`** → runs for ticks, writes `battle_report.json`, and flags tempo spikes.  
- **`aggregate_delta`** → groups 16 reports into a Delta summary with trust ratings.  

---

### 5. Quality Gate (Linter) Hooks

The **Linter** runs automatically after `simulate_alfa` completes:

1. Loads result and validates against `report.schema.json` to protect trust.  
2. Checks **entropy**, **diversity**, and **stability** so terrain tempo stays healthy.  
3. Marks Alfa as **green**, **amber**, or **red** in its `manifest.json`, guiding which squads rotate in next.  

---

### 6. Naming & Folder Rules

| Type | Pattern  | Example |
|------|----------|---------|
| **Alfa folders** | `alfas/alfa_{4-digit-id}_{slug}/` | `alfas/alfa_0023_mind_of_valor/` |
| **Templates** | `templates/{type}_template/` | `templates/alfa_template/` |
| **Recipes** | `recipes/{category}_{action}.yml` | `recipes/forge_mint_alfa.yml` |

---

### 7. Quick Start (3 Commands)

```bash
forge mint_alfa coords=23,7 workspace=toysoldiers_ai_0
forge simulate_alfa id=alfa_0023 ticks=128
forge aggregate_delta delta=delta_13
```

Run the trio to seed terrain, set tempo, and brief the squad without delay.

---

### Field Insight

Keep the pantry stocked and the recipes rehearsed so squads trust every bite of terrain they’re served.
