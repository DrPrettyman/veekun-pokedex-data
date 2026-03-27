# pokedata3g — Project Plan

## Core Principle

**Minimize hardcoded game data in TypeScript.** The Python pipeline and `data.json` are the single source of truth for game mechanics. The TypeScript module should be a generic rules engine that reads and interprets data, not a place where game knowledge is embedded.

The test: *"If we added another item, move, or Pokemon, could we just add it to data.json, or would we have to edit the TypeScript?"* If the answer is "edit TS", push the knowledge into data.json. Things not in the CSVs can be hardcoded in Python and written to JSON — the goal is avoiding hardcoding in TS specifically.

---

## What's done

### Data pipeline (Python)
- 15 `build_xxx()` functions extract all Gen 3 data from veekun CSVs
- 386 species, 354 moves (Gen 3-corrected), 18 types, 25 natures, 76 abilities, 180 items, 43 berries, 58 TMs/HMs, 16 status conditions
- Item effects: `item_effects.json` — all mechanically important categories
- Ability effects: `ability_effects.json` — trigger/effect/args for all 76 Gen 3 abilities
- `battleConfig` and `weatherMechanics` in data.json
- Species-level `fixedHp`, move-level `flagIds` (including contact flag)

### npm module (TypeScript, ~9,500 lines, 86 tests)

### Battle system — implemented mechanics

**Core:** Damage formula, accuracy, status conditions (8), weather (4 + duration + suppression), field effects (Reflect, Light Screen, Safeguard, Mist, Spikes)

**Abilities (76, all data-driven):** Damage modifiers, type immunity, stat multipliers, status immunity, stat drop immunity, speed/weather, switch-in (Intimidate, weather), contact (Static, Poison Point, Flame Body, Rough Skin), turn-end (Speed Boost, Shed Skin, Rain Dish), and many more

**Move mechanics:**
- Two-turn, Protect/Detect/Endure, rampage (Thrash/Outrage), partial trapping (Wrap/Bind/Fire Spin)
- Counter, Mirror Coat, Baton Pass, Rapid Spin, Mean Look/Spider Web/Block
- Perish Song, Destiny Bond, Grudge, Focus Energy
- Rest, Heal Bell/Aromatherapy, Belly Drum, Pain Split
- Substitute (absorbs damage, blocks status), Curse (Ghost + non-Ghost variants)
- Wish (delayed heal), Future Sight/Doom Desire (delayed damage), Yawn (delayed sleep)
- Trick (swap held items), Disable, Encore, Torment, Taunt
- Force switch, OHKO, Struggle, multi-hit, contact flag enforcement

**Other:** Held items (20+), Pokeballs (full formula), EXP/EV distribution, Player integration (catch → party/storage), breeding/daycare/eggs

---

## What's left

### Phase 2 — Data-driven status conditions and move effects (cleanup)

Move remaining hardcoded effectId if/else chains and status ID constants into data.json.

- [ ] Status condition `mechanics` field — preventAction, endOfTurnDamage, duration, selfHit, thawChance
- [ ] `moveEffectMechanics` in data.json — replace effectId if/else with data dispatch
- [ ] Refactor battle.ts to read these generically

### Remaining niche moves

- [ ] Mimic, Sketch, Transform, Sleep Talk, Metronome — move copying/randomization
- [ ] Conversion, Conversion 2, Camouflage — type changing
- [ ] Stockpile / Spit Up / Swallow — stacking mechanic
- [ ] Memento — faint + lower opponent stats
- [ ] Ingrain, Magic Coat, Imprison, Refresh, Recycle, Snatch

### Polish

- [ ] Close remaining item data gaps (loot, collectibles, fossils)
- [ ] Encounter/location data extraction from veekun CSVs
- [ ] Move/ability descriptions in data.json
- [ ] npm publish prep

---

## Design principle recap

| Layer | Responsibility |
|-------|---------------|
| **veekun CSVs** | Raw source of truth |
| **Python pipeline** | Extract, transform, curate. All game knowledge lives here. |
| **data.json** | Complete, self-describing game data + mechanics |
| **TypeScript engine** | Generic interpreter. Reads data.json. No Pokemon-specific knowledge. |
