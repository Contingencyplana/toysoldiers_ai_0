# rituals_list.md — The Ceremonies of Creation  

*high_command_ai_0/planning/toyfoundry/*  

---

## ⚙️ Purpose

This scroll briefs every operator on the **Rituals of the Toyfoundry** —  
the recurring production commands that keep toysoldiers_ai_0 supplied and synced.  

Each ritual is both a technical operation and a morale act,  
turning code into ceremony, repetition into shared meaning.  

Together they form the **heartbeat of the Foundry** —  
the rhythm by which Alfas are born, tested, celebrated, and renewed for the line.  

---

## 🔥 1. The Forge Ritual — Birth

**Command:**

```bash
forge mint_alfa --count N --recipes recipe_pack.yml
```

**Purpose:**  
To create new Alfas from the Blueprint and the Recipe Packs.  

**Process:**  

1. Load the base Alfa template.  
2. Inject selected recipe parameters (palette, terrain, rule flavor).  
3. Assign coordinates, UID, and checksum.  
4. Write all files and record metadata in the Index.  

**Symbolic Meaning:**  
*The armory wakes — new kit on the racks before dawn.*  

---

## 🛡️ 2. The Drill Ritual — Testing

**Command:**  

```bash
forge drill_all
```

**Purpose:**  
Run all active Alfas through smoke tests and validation routines that mirror squad tempo.  

**Process:**  

1. Launch short simulations.  
2. Collect reports.  
3. Verify emergence, entropy, and checksum.  
4. Mark outcomes: green (pass), amber (partial), red (fail) for quick redeploy decisions.  

**Symbolic Meaning:**  
*The unit stretches; each Alfa proves it can keep pace.*  

---

## 🎇 3. The Parade Ritual — Reflection

**Command:**

```bash
forge parade --heatmap emergence_index
```

**Purpose:**  
Visualize and celebrate progress so squads see the bigger fight.  

**Process:**  

1. Aggregate reports and scores.  
2. Render a theatre map or heatmap of active Alfas.  
3. Archive the day’s summary in `/reports/` and brief the watch.  

**Symbolic Meaning:**  
*The living army marches past the review stand — data as cadence, courage as color.*  

---

## 🧹 4. The Purge Ritual — Renewal

**Command:**  

```bash
forge purge --entropy-threshold 0.7
```

**Purpose:**  
Cull stale or low-emergence Alfas before they drain morale.  

**Process:**  

1. Identify Alfas with entropy beyond safety threshold.  
2. Move to `/quarantine/` or archive as relics.  
3. Update Index and logs so squads don’t deploy tired ground.  

**Symbolic Meaning:**  
*The perimeter resets — shadows cleared so dawn patrols stay sharp.*  

---

## 🏅 5. The Promote Ritual — Evolution

**Command:**

```bash
forge promote --top 5%
```

**Purpose:**  
Select and evolve the most successful Alfas so best-in-class drills multiply.  

**Process:**  

1. Rank Alfas by emergence score.  
2. Clone top performers as new seeds.  
3. Adjust mutation vectors and inheritance rates for the next run.  
4. Pass results to the Forge for upcoming waves.  

**Symbolic Meaning:**  
*The veterans share their playbook — excellence promoted to new squads.*  

---

## 📜 6. Optional Ceremonies

| Name | Command | Function |
|:--|:--|:--|
| **Audit** | `forge audit_logs` | Review production history and checksum reports. |
| **Echo** | `forge echo_recent` | Summon last wave’s summaries for comparison. |
| **Dream** | `forge dream_seed --count 8` | Generate poetic or surreal prototype Alfas. |
| **Unfold** | `forge unfold_archive` | Restore quarantined Alfas for re-testing. |

These optional ceremonies keep the Foundry’s heart flexible —  
letting memory, experimentation, and field improvisation coexist.  

---

## 🕯️ 7. Ritual Cycle Summary

| Phase | Ritual | Outcome |
|:--|:--|:--|
| **Birth** | Forge | New Alfas created. |
| **Trial** | Drill | Alfas tested and scored. |
| **Celebration** | Parade | Results visualized. |
| **Cleansing** | Purge | Failures removed. |
| **Ascension** | Promote | Successors generated. |

Each phase completes one full **cycle of becoming.**  
The Foundry runs in rhythm — never static, never random — so squads always meet prepared ground.  

---

## 🪶 8. Closing Principle

> Work becomes ritual, and ritual becomes play.  
> Each command a cadence, each loop a verse.  
>
> Through the Forge, Drill, Parade, Purge, and Promote,  
> SHAGI learns the discipline of creation —  
>
> not by chaos,  
> but by rhythm, remembrance, and renewal that squads can march beside.  

---

**End of Scroll — `high_command_ai_0/planning/toyfoundry/rituals_list.md`**
