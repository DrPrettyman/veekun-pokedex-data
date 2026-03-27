# pokedata3g — Project Plan

## Core Principle

**Minimize hardcoded game data in TypeScript.** The Python pipeline and `data.json` are the single source of truth for game mechanics. The TypeScript module should be a generic rules engine that reads and interprets data, not a place where game knowledge is embedded.

The test: *"If we added another item, move, or Pokemon, could we just add it to data.json, or would we have to edit the TypeScript?"* If the answer is "edit TS", push the knowledge into data.json. Things not in the CSVs can be hardcoded in Python and written to JSON — the goal is avoiding hardcoding in TS specifically.

---

## What's done

### Data pipeline (Python)
- 15 `build_xxx()` functions extract all Gen 3 data from veekun CSVs
- 386 species, 354 moves (Gen 3-corrected), 18 types, 25 natures, 76 abilities, 180 items, 43 berries, 58 TMs/HMs, 16 status conditions
- Item effects: `item_effects.json` covering all mechanically important categories
- Ability effects: `ability_effects.json` with trigger/effect/args for all 76 Gen 3 abilities
- `battleConfig` and `weatherMechanics` in data.json — battle constants are data, not hardcoded in TS
- Species-level `fixedHp` field (Shedinja) — data-driven

### npm module (TypeScript, ~8,500 lines, 81 tests)
- `Pokemon`, `Battle`, `Party`, `Bag`, `Player`, `Daycare`, `Egg`, `PokemonStorage`, `ItemStorage`
- `abilityEffects.ts` — generic ability handler reading from data.json
- Battle accepts `Player` or raw `Pokemon[]`; catch places Pokemon in party or PC storage

### Battle system — implemented mechanics

**Core:**
- Damage formula (crits, STAB, effectiveness, weather, held items, ability modifiers, screens)
- Accuracy (stat stages, held item penalties, ability modifiers like Compound Eyes)
- Status conditions: all 8 with battle behavior
- Weather: all 4 types, 5-turn duration from moves, permanent from BattleOptions, suppression (Cloud Nine/Air Lock)

**Field effects:**
- Reflect, Light Screen, Safeguard, Mist, Spikes (layers + type/ability immunity)

**Move mechanics:**
- Two-turn moves (8 moves: Fly/Dig/Dive/Bounce/SolarBeam/SkullBash/SkyAttack/RazorWind)
- Protect / Detect / Endure (with consecutive-use penalty)
- Rampage moves (Thrash/Outrage/Petal Dance — locked 2-3 turns + confusion)
- Partial trapping (Wrap/Bind/Fire Spin/Clamp/Sand Tomb/Whirlpool — trap + DOT)
- Counter / Mirror Coat (reflect 2x physical/special damage)
- Baton Pass (switch preserving stat stages)
- Rapid Spin (clear Spikes + trapping from own side)
- Mean Look / Spider Web / Block (prevent switching)
- Perish Song (3-turn countdown, both faint at 0)
- Destiny Bond (opponent faints if user faints)
- Focus Energy (+2 crit stage)
- Rest (full heal + forced 2-turn sleep)
- Heal Bell / Aromatherapy (cure party status)
- Belly Drum (lose 50% HP, max Attack)
- Pain Split (average HP)
- Unique: Disable, Encore, Torment, Taunt
- Force switch (Roar/Whirlwind), OHKO, Struggle, multi-hit distribution

**Abilities (76 abilities, all data-driven):**
- Damage: Huge Power, Pure Power, Hustle, Guts, Marvel Scale, Thick Fat, Overgrow/Blaze/Torrent/Swarm
- Immunity: Levitate, Volt Absorb, Water Absorb, Flash Fire, Wonder Guard
- Status: Limber, Insomnia, Immunity, Oblivious, Own Tempo, Magma Armor, Water Veil
- Battle: Intimidate, Clear Body, Hyper Cutter, Keen Eye, Inner Focus, Sturdy, Rock Head, Shield Dust, Serene Grace
- Speed: Swift Swim, Chlorophyll, Speed Boost
- Weather: Drizzle, Drought, Sand Stream, Cloud Nine, Air Lock
- Contact: Static, Poison Point, Flame Body, Cute Charm, Effect Spore, Rough Skin
- Turn-end: Speed Boost, Shed Skin, Rain Dish
- Other: Pressure (2x PP), Shadow Tag, Arena Trap, Run Away, Early Bird, Liquid Ooze, Battle Armor/Shell Armor

**Other systems:**
- Held items (20+ effects), Pokeballs (full catch formula), EXP/EV distribution, breeding/daycare/eggs

---

## What's left

### Phase 2 — Data-driven status conditions and move effects (cleanup)

Move the remaining hardcoded effectId if/else chains and status ID constants into data.json. Not adding functionality — restructuring for extensibility.

- [ ] Status condition `mechanics` field in data.json — preventAction chance, endOfTurnDamage fraction, duration range, selfHit power, thawChance, statModifier
- [ ] `moveEffectMechanics` in data.json — tag effect IDs with behavior descriptors so the TS dispatches on data instead of `if (effectId === 87)` chains
- [ ] Refactor battle.ts to read these generically

### Phase 5 — Remaining battle mechanics

Still not implemented:

- [ ] **Substitute** (effectId 80) — absorbs damage until broken, 25% HP cost
- [ ] **Wish** (effectId 180) — delayed heal 2 turns later
- [ ] **Future Sight / Doom Desire** (effectId 149) — delayed damage 2 turns later
- [ ] **Curse** (effectId 110) — different behavior for Ghost vs non-Ghost
- [ ] **Trick** (effectId 178) — swap held items
- [ ] **Grudge** (effectId 195) — drain PP on faint
- [ ] **Yawn** (effectId 188) — delayed sleep
- [ ] **Encore** already works but **Mimic, Sketch, Transform, Sleep Talk, Metronome** are niche
- [ ] Contact move flag — currently contact abilities trigger on all damage; should check move's contact flag

### Phase 6 — Polish

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
