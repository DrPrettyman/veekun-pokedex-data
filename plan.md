# pokedata3g — Project Plan

## Core Principle

**Minimize hardcoded game data in TypeScript.** The Python pipeline and `data.json` are the single source of truth for game mechanics. The TypeScript module should be a generic rules engine that reads and interprets data, not a place where game knowledge is embedded. This makes the system extensible and keeps all Pokemon-specific logic in one place.

The test: *"If we added another item, move, or Pokemon, could we just add it to data.json, or would we have to edit the TypeScript?"* If the answer is "edit TS", push the knowledge into data.json.

---

## What's done

### Data pipeline (Python) — complete and stable
- 15 `build_xxx()` functions extract all Gen 3 data from veekun CSVs
- 386 species, 354 moves (Gen 3-corrected), 18 types, 25 natures, 77 abilities, 180 items, 43 berries, 58 TMs/HMs, 16 status conditions
- Item effect codification covers all mechanically important categories
- `generate.py` produces a 1.2 MB `data.json`
- Species-level `fixedHp` field (Shedinja) — data-driven, no hardcoded species ID in TS

### npm module (TypeScript, ~7,500 lines, 71 tests)
- `Pokemon`, `Battle`, `Party`, `Bag`, `Player`, `Daycare`, `Egg`, `PokemonStorage`, `ItemStorage`
- Battle accepts `Player` or raw `Pokemon[]`; catch places Pokemon in party or PC storage
- Item/held-item effect systems are data-driven via `item_effects.json`

### Battle system — implemented mechanics
- **Damage formula**: crits, STAB, effectiveness, weather modifiers, held item boosts, screens, burn halving attack
- **Status conditions**: paralysis (speed/action), burn (DOT + atk halve), sleep/freeze/confusion/attraction (action prevention), toxic (scaling DOT)
- **Weather**: all 4 types with type boosts, DOT, immunities; **5-turn duration** from moves, permanent from BattleOptions
- **Field effects**: Reflect, Light Screen, Safeguard, **Mist** (blocks opponent stat reductions), Spikes (layers + flying immunity)
- **Two-turn moves**: Fly/Dig/Dive/Bounce (semi-invulnerable), SolarBeam/SkullBash/SkyAttack/RazorWind (charge-only), SolarBeam sun skip, SkullBash +1 Def
- **Protect / Detect**: blocks all opponent moves; consecutive use halves success chance
- **Endure**: survive any hit at 1 HP; shares consecutive-use penalty with Protect
- **Unique moves**: Disable, Encore, Torment, Taunt
- **Held items**: 20+ effects (type boosts, stat multipliers, berries, Focus Band, Choice Band lock, King's Rock, Quick Claw, Leftovers, etc.)
- **Pokeballs**: full Gen 3 catch formula, catch places into player party or PC storage
- **EXP/EV distribution**: participant tracking, Exp Share splitting
- **Other**: Struggle, flee formula, force switch (Roar/Whirlwind), OHKO moves, multi-hit distribution

---

## What's left

### Hardcoded game data to move into data.json

~100+ hardcoded constants in TS that violate the core principle. These need to become data:

**Move effect IDs** — two-turn `[156, 257, 256, 264, 152, 76, 146, 40]`, unique `[87, 91, 166, 176, 112, 117]`, field `[66, 36, 125, 47, 113]` all in if/else chains. Should be `moveEffectMechanics` in data.json with behavior tags (`twoTurn`, `semiInvulnerable`, `field`, `unique`).

**Status mechanics** — IDs duplicated across files, behavior hardcoded (freeze 20% thaw, confusion 50% self-hit, etc.). Should be `mechanics` field on each status condition entry.

**Weather interactions** — type ID checks for boosts/weakens/immunities. Should be `weatherMechanics` in data.json.

**Battle formula constants** — STAB 1.5x, crit 2x, crit odds table, multi-hit distribution, flee formula, Spikes fractions, Struggle power/recoil, confusion self-hit power. Should be `battleConfig` in data.json.

**Pokemon-specific** — Luxury Ball ID (11) for happiness, evolution trigger IDs, PP Up formula, happiness thresholds. Should be data-driven fields.

### Missing battle mechanics

**Not implemented at all:**
- **Abilities** — the single biggest gap. Nothing in battle reads abilities. No Levitate, Intimidate, Wonder Guard, Huge Power, Guts, Flash Fire, Static, etc. Should follow the held-item trigger/effect/args pattern as `abilityEffects` in data.json.
- **Counter / Mirror Coat** — reflect physical/special damage back
- **Baton Pass** — switch while preserving stat stages
- **Rapid Spin** — clear entry hazards from own side
- **Trapping** (Mean Look, Spider Web, Wrap/Bind/Fire Spin) — prevent switching
- **Delayed effects** (Wish, Future Sight, Doom Desire, Perish Song) — turn-delayed system
- **Destiny Bond / Grudge** — mutual faint / PP drain on faint
- **multiTurn** — Thrash/Outrage (locked attack + confusion), trapping moves (partial DOT)
- **~20 more unique effects** (Substitute, Rest, Focus Energy, Haze, Trick, etc.)

---

## Phases

### Phase 1 — Data-driven battle config and weather

Push battle constants and weather mechanics into data.json so the TS reads them generically.

- [ ] `battleConfig` in data.json — STAB, crit, damage roll, flee formula, Spikes fractions, etc.
- [ ] `weatherMechanics` in data.json — type boosts/weakens, DOT, immunities, default duration
- [ ] Refactor battle.ts to read these from data instead of hardcoded constants
- [ ] Move Luxury Ball ID, PP Up formula, happiness thresholds to data

### Phase 2 — Data-driven status conditions and move effects

- [ ] Status condition `mechanics` field — preventAction, endOfTurnDamage, duration, selfHit, thawChance, statModifier
- [ ] `moveEffectMechanics` in data.json — tag effect IDs with behavior descriptors
- [ ] Refactor battle.ts to dispatch on data instead of effectId if/else chains
- [ ] Refactor status handling to read mechanics instead of hardcoded condition IDs

### Phase 3 — Abilities

The biggest missing feature. Follow the held-item pattern:

- [ ] `abilityEffects` in data.json (or `ability_effects.json` like `item_effects.json`)
- [ ] Generic ability handler in TS modeled on `heldItemEffects.ts`
- [ ] Wire into Battle: damage calc, status application, switch-in, end-of-turn, contact
- [ ] Key abilities: Levitate, Intimidate, Huge Power, Guts, Wonder Guard, Flash Fire, Static, Thick Fat, Swift Swim, etc.

### Phase 4 — Remaining battle mechanics

With the data-driven architecture in place, each of these is a data entry + small generic handler:

- [ ] multiTurn moves (Thrash/trapping — locked attack + confusion/DOT)
- [ ] Counter / Mirror Coat (reflect damage)
- [ ] Baton Pass (preserve stat stages on switch)
- [ ] Rapid Spin (clear hazards)
- [ ] Trapping (prevent switching)
- [ ] Delayed effects (Wish, Future Sight, Perish Song)
- [ ] Remaining unique effects (Substitute, Rest, Focus Energy, Haze, etc.)

### Phase 5 — Polish

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
