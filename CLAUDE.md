# veekun-pokedex-data

Pokemon data extraction pipeline targeting **Generation 3** (Ruby/Sapphire/Emerald/FireRed/LeafGreen). Reads veekun CSV files and produces structured Python dicts and a compact JSON module for npm.

## Project Structure

```
python/                         # All Python source, data, and assets
  lookups.py                    # build_xxx() functions that read CSVs -> dict[int, dict]
  coagulate.py                  # Module-level constants (POKEMON, MOVES, TYPES, etc.) + ID_TO_NAME
  items.py                      # Item processing: RAW_ITEMS + item_effects.json -> ITEMS
  item_effects.json             # Hand-curated structured effects, keyed by category_id
  item_notes.md                 # Detailed notes on item categories and codification plans
  generate.py                   # Produces pokedata3g/src/data.json from coagulate data
  build_item_icons.py           # Builds item icon sprites from decomp assets
  assets/
    veekun-csv/                 # Raw veekun CSV data (read-only source of truth)
    sprites/                    # Pokemon sprite PNGs (front, back, shiny, icon, footprint)
    item-sprites-raw/           # Decomp item icon assets (emerald, firered)
pokedata3g/                     # npm module output (TypeScript + JSON + sprites)
pokedex.ipynb                   # Jupyter notebook for interactive exploration
```

## Key Conventions

### Gen 3 Filtering
- Version group IDs: **5** (RSE), **6** (FRLG), **7** (Emerald) — use `version_group_id.isin((5, 6, 7))`
- Version IDs: **7-11** for version-specific data (flavor text, held items)
- Generation filter: `generation_id <= 3`
- English language: `local_language_id == 9`
- When deduplicating across versions, sort by version_group_id descending and keep first (latest Gen 3 data)

### Data Architecture
- `python/lookups.py` contains all `build_xxx()` functions. Each reads CSVs, merges English names/prose, and returns `dict[int, dict]` keyed by primary ID.
- `python/coagulate.py` calls these at module level to create constants: `POKEMON`, `MOVES`, `TYPES`, `NATURES`, `ABILITIES`, `ITEMS`, `BERRIES`, `STATS`, `MACHINES`, `MOVE_FLAGS`, `ITEM_FLAGS`, `CONTEST_EFFECTS`.
- `coagulate.ID_TO_NAME` is a dict of dicts mapping `{category: {id: name}}` for 22+ categories.
- `coagulate.DAMAGE_TABLE` and `damage_multiplier()` provide type effectiveness lookups.
- Entry scripts (`generate.py`, `build_item_icons.py`) chdir to `python/` so `assets/` paths resolve correctly. Paths to `pokedata3g/` use `../`.

### Custom Stat IDs (in build_stats)
Veekun stats go 1-8. We added custom entries:
- **0**: Level
- **9** (max_id + 1): PP (select move)
- **10** (max_id + 2): PP (all moves)
- **11** (max_id + 3): Happiness

These are used in item_effects.json to reference what a vitamin/item affects.

### Item Effects System
`python/item_effects.json` is keyed by **category_id** (string, JSON limitation). Each entry:
```json
{
  "category_name": "Human-readable name",
  "description": "How to interpret the effects field",
  "effects": {
    "item_id": <effect_data>
  }
}
```
Effect format varies by category — the `description` field documents each one. `items.py` generically loops all categories and merges effects into RAW_ITEMS to build ITEMS.

See `python/item_notes.md` for detailed plans on remaining categories.

### Pokemon Forms
Multi-form Pokemon (Deoxys, Unown, Castform) use form-keyed dicts:
- `{0: value}` = all forms share the same data
- `{1: val, 2: val, ...}` = per-form data (1-indexed)

Form-varying fields: `type_ids`, `stats`, `ev_yields`, `level_moves`, `teachable_moves`, `egg_moves`, `identifier`

### Move Changelog
`build_moves()` applies `move_changelog.csv` to revert post-Gen 3 stat changes (power, pp, accuracy, etc.) so moves reflect their Gen 3 values.

## Common Tasks

### Adding a new item effects category
1. Look up the category_id in `python/assets/veekun-csv/item_categories.csv`
2. Add an entry to `python/item_effects.json` with effects keyed by item_id
3. No code changes needed — `items.py` picks it up automatically

### Adding a new data lookup
1. Add `build_xxx()` function to `lookups.py`
2. Add `XXX = lookups.build_xxx()` constant to `coagulate.py`
3. Optionally add to `build_id_to_name()` if it has names

### Regenerating the npm module
```bash
python python/generate.py
```
Note: `generate.py` still uses `coagulate.Pokemon()` — this should be updated to use `coagulate.POKEMON`.

## Running
```bash
# Interactive exploration
jupyter notebook pokedex.ipynb

# Quick test
python -c "import sys; sys.path.insert(0,'python'); import coagulate; print(len(coagulate.POKEMON), 'pokemon')"
python -c "import sys; sys.path.insert(0,'python'); import items; print(len(items.ITEMS), 'items with effects')"
```
