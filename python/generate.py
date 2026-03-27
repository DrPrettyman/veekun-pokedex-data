#!/usr/bin/env python3
"""Generate compact Pokemon JSON for the pokedata3g npm module."""

import csv
import json
import os
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

import coagulate


# Map evolution dict keys to short camelCase keys
EVOLUTION_KEY_MAP = {
    'to_species_id': 'to',
    'trigger_id': 'trigger',
    'minimum_level': 'level',
    'trigger_item_id': 'triggerItem',
    'held_item_id': 'heldItem',
    'known_move_id': 'knownMove',
    'minimum_happiness': 'happiness',
    'minimum_beauty': 'beauty',
    'time_of_day': 'timeOfDay',
    'gender_id': 'gender',
    'location_id': 'location',
    'trade_species_id': 'tradeSpecies',
}


def stats_to_array(stat_dict):
    """Convert {stat_id: value} dict to [HP, Atk, Def, SpA, SpD, Spe] array."""
    return [stat_dict.get(i, 0) for i in range(1, 7)]


def ev_yields_to_sparse(ev_dict):
    """Convert {stat_id: value} to {"stat_id": value} with string keys, only non-zero."""
    return {str(k): v for k, v in ev_dict.items() if v}


def compact_abilities(abilities_list):
    """Encode abilities as signed ints: positive = normal, negative = hidden."""
    return [
        -a['ability_id'] if a['is_hidden'] else a['ability_id']
        for a in abilities_list
    ]


def compact_evolution(ev):
    """Shorten evolution keys."""
    return {EVOLUTION_KEY_MAP[k]: v for k, v in ev.items() if k in EVOLUTION_KEY_MAP}


def snake_to_camel(s):
    """Convert snake_case to camelCase."""
    first, *rest = s.split('_')
    return first + ''.join(w.capitalize() for w in rest)


def snake_to_camel_keys(d: dict, include_keys: list = None) -> dict:
    if include_keys is None:
        include_keys = set(d.keys())
    
    new_d = dict()
    
    for k, v in d.items():
        
        if k not in include_keys:
            continue
        
        if isinstance(k, str):
            new_k = snake_to_camel(k)
        else:
            new_k = str(k)
            
        if isinstance(v, dict):
            new_d[new_k] = snake_to_camel_keys(v)
        elif isinstance(v, list):
            new_v = []
            for item in v:
                if isinstance(item, dict):
                    new_v.append(snake_to_camel_keys(item))
                else:
                    new_v.append(item)
            new_d[new_k] = new_v
        else:
            new_d[new_k] = v
            
    return new_d


def get_all_keys(source: list[dict]):
    keys = set()
    for d in source:
        keys.update(d.keys())
    return keys


def keyed_collection(source: list[dict], key: str | int = 'id', include_keys: list = None):
    if isinstance(source, dict):
        source = list(source.values())
    if include_keys is None:
        include_keys = get_all_keys(source)
    collection = dict()
    for d in source:
        if d.get(key) is None:
            continue
        collection[d[key]] = snake_to_camel_keys(d, include_keys=include_keys)
    return collection


def compact_form_data(form_dict, transform=None):
    """Flatten single-form data; keep dict with string keys for multi-form.

    Single form:  {0: [1, 3]}           -> [1, 3]
    Multi-form:   {1: [1, 3], 2: [1, 14]} -> {"1": [1, 3], "2": [1, 14]}
    With transform: {0: {1: 50, 2: 60}}, transform=stats_to_array -> [50, 60, 0, 0, 0, 0]
    """
    if len(form_dict) == 1 and 0 in form_dict:
        val = form_dict[0]
        return transform(val) if transform else val
    result = {}
    for fk, v in form_dict.items():
        result[str(fk)] = transform(v) if transform else v
    return result


def generate():
    output = {"species": {}}

    for d in coagulate.POKEMON.values():
        is_multi = d['forms'] != [0]

        entry = {
            'name': d['name'],
            'identifier': compact_form_data(d['identifier']),
            'genus': d['genus'],
            'flavorText': d['flavor_text'],
            'height': d['height'],
            'weight': d['weight'],
            'types': compact_form_data(d['type_ids']),
            'stats': compact_form_data(d['stats'], stats_to_array),
            'evYields': compact_form_data(d['ev_yields'], ev_yields_to_sparse),
            'abilities': compact_abilities(d['abilities']),
            'baseExp': d['base_experience'],
            'captureRate': d['capture_rate'],
            'baseHappiness': d['base_happiness'],
            'growthRate': d['growth_rate_id'],
            'genderRate': d['gender_rate'],
            'eggGroups': d['egg_group_ids'],
            'hatchCounter': d['hatch_counter'],
            'color': d['color_id'],
            'shape': d['shape_id'],
            'habitat': d['habitat_id'],
            'isBaby': d['is_baby'],
            'hasGenderDiff': d['has_gender_differences'],
            'evolvesFrom': d['evolves_from_species_id'],
            'evoChain': d['evolution_chain_id'],
            'formsSwitchable': d['forms_switchable'],
            'levelMoves': compact_form_data(d['level_moves']),
            'teachMoves': compact_form_data(d['teachable_moves']),
            'eggMoves': compact_form_data(d['egg_moves']),
            'evolutions': [compact_evolution(ev) for ev in d['evolutions']],
            'heldItems': [[h['item_id'], h['rarity']] for h in d['held_items']],
        }

        # Sprites: convert paths to be relative to the module's sprites/ dir
        sprites = d.get('sprites', {})
        compact_sprites = {}
        for sprite_type in ('front', 'back', 'front_shiny', 'back_shiny', 'icon', 'footprint'):
            val = sprites.get(sprite_type)
            if val is None:
                continue
            if isinstance(val, str):
                # Single path -> just the filename
                compact_sprites[sprite_type] = os.path.basename(val)
            elif isinstance(val, dict):
                compact_sprites[sprite_type] = {
                    str(k): os.path.basename(v) for k, v in val.items()
                }
        entry['sprites'] = compact_sprites

        # Species with a fixed HP value (e.g. Shedinja always has 1 HP)
        if d['id'] == 292:  # Shedinja
            entry['fixedHp'] = 1

        if is_multi:
            entry['forms'] = d['forms']
            if d['form_identifier']:
                entry['formIdentifier'] = {
                    str(k): v for k, v in d['form_identifier'].items()
                }
            if d['form_name']:
                entry['formName'] = {
                    str(k): v for k, v in d['form_name'].items()
                }

        output['species'][str(d['id'])] = entry

    
    # Experience tables: {growthRateId: [exp_for_level_1, ..., exp_for_level_100]}
    exp_tables = {}
    with open('assets/veekun-csv/experience.csv') as f:
        for row in csv.DictReader(f):
            gid = row['growth_rate_id']
            if gid not in exp_tables:
                exp_tables[gid] = [0] * 100
            exp_tables[gid][int(row['level']) - 1] = int(row['experience'])
    output['experience'] = exp_tables

    output['natures'] = keyed_collection(coagulate.NATURES)
    output['machines'] = keyed_collection(coagulate.MACHINES, key = "machine_number")
    output['stats'] = keyed_collection(coagulate.STATS)
    output['types'] = keyed_collection(coagulate.TYPES)
    output['berries'] = keyed_collection(coagulate.BERRIES)
    output['statusConditions'] = keyed_collection(coagulate.STATUS_CONDITIONS)
    output['itemFlags'] = keyed_collection(coagulate.ITEM_FLAGS)
    output['moves'] = keyed_collection(coagulate.MOVES, include_keys=[
        "id", "name", "type_id", "pp", "power", "accuracy",
        "priority", "target_id", "effect_id", "effect_chance",
        "category_id", "ailment_id", "min_hits", "max_hits", "min_turns", "max_turns",
        "drain", "healing", "crit_rate", "ailment_chance", "flinch_chance", "stat_chance",
        "stat_changes", "flag_ids",
    ])
    # Items: all Gen 3 items with metadata + structured effects where available
    with open(os.path.join(SCRIPT_DIR, 'item_effects.json')) as f:
        item_effects_data = json.load(f)

    def load_effects(key):
        return {
            int(k): v for k, v in item_effects_data[key].items()
            if not k.startswith('_')
        }

    pokemon_effects = load_effects('pokemonEffects')
    battle_effects = load_effects('battleEffects')
    overworld_effects = load_effects('overworldEffects')
    held_effects = load_effects('heldEffects')

    # Build machine-by-item lookup for TM/HM pokemonEffects
    machine_by_item = {m['item_id']: m for m in coagulate.MACHINES.values()}

    all_items = {}
    for item_id, item in coagulate.ITEMS.items():
        icon_file = f"{item['identifier']}.png"
        icon_path = os.path.join('assets', 'sprites', 'item', icon_file)
        entry = {
            'name': item['name'],
            'identifier': item['identifier'],
            'categoryId': item['category_id'],
            'pocketId': item['pocket_id'],
            'cost': item['cost'],
            'flagIds': item['flag_ids'],
            'icon': icon_file if os.path.exists(icon_path) else None,
        }
        if item_id in pokemon_effects:
            entry['pokemonEffects'] = pokemon_effects[item_id]
        elif item_id in machine_by_item:
            machine = machine_by_item[item_id]
            tm_effects = {
                'target': 'partyMember',
                'effects': [{'effect': 'teachMove', 'args': {'moveId': machine['move_id']}}],
            }
            if machine['machine_number'] > 100:  # HMs are reusable
                tm_effects['reusable'] = True
            entry['pokemonEffects'] = tm_effects
        if item_id in battle_effects:
            entry['battleEffects'] = battle_effects[item_id]
        if item_id in overworld_effects:
            entry['overworldEffects'] = overworld_effects[item_id]
        if item_id in held_effects:
            entry['heldEffects'] = held_effects[item_id]
        all_items[str(item_id)] = entry

    output['items'] = all_items

    # Item pockets: {id: {identifier, name}}
    import pandas as pd
    pockets_df = pd.read_csv('assets/veekun-csv/item_pockets.csv')
    pocket_names = pd.read_csv('assets/veekun-csv/item_pocket_names.csv')
    pocket_names_en = pocket_names[pocket_names['local_language_id'] == 9]
    pockets_df = pockets_df.merge(pocket_names_en[['item_pocket_id', 'name']], left_on='id', right_on='item_pocket_id')
    output['pockets'] = {
        str(row['id']): {'identifier': row['identifier'], 'name': row['name']}
        for _, row in pockets_df.iterrows()
    }

    # Abilities: base data + structured effects
    with open(os.path.join(SCRIPT_DIR, 'ability_effects.json')) as f:
        ability_effects_data = json.load(f)

    all_abilities = {}
    for ability_id, ability in coagulate.ABILITIES.items():
        entry = {
            'identifier': ability['identifier'],
            'name': ability['name'],
            'shortEffect': ability.get('short_effect', ''),
        }
        effects = ability_effects_data.get(str(ability_id))
        if effects and 'effects' in effects:
            entry['effects'] = effects['effects']
        all_abilities[str(ability_id)] = entry
    output['abilities'] = all_abilities

    # ID-to-name lookup: {category: {id: name}}
    output['idToName'] = {}
    for category, mapping in coagulate.ID_TO_NAME.items():
        output['idToName'][category] = {str(k): v for k, v in mapping.items()}

    # Battle config: constants that the TS engine reads instead of hardcoding
    output['battleConfig'] = {
        'stabMultiplier': 1.5,
        'critMultiplier': 2,
        'damageRollMin': 85,
        'damageRollRange': 16,  # 85 + random(0..15) = 85..100
        'critOdds': [16, 8, 4, 3, 2],  # denominator per crit stage 0-4
        'maxCritStage': 4,
        'maxStatStage': 6,
        'minStatStage': -6,
        'multiHitWeights': [0.375, 0.375, 0.125, 0.125],  # for 2, 3, 4, 5 hits
        'struggle': {'power': 50, 'recoilFraction': 0.25},
        'confusionSelfHitPower': 40,
        'fleeFormula': {
            'speedMultiplier': 128,
            'attemptBonus': 30,
            'threshold': 256,
        },
        'spikesDamageFractions': [0, 0.125, 1/6, 0.25],  # layers 0-3
        'spikesImmuneTypeIds': [3],  # Flying
        'trainerExpBonus': 1.5,
        'weatherDuration': 5,  # turns when set by a move
        'luxuryBallId': 11,
        'maxEvPerStat': 255,
        'maxEvTotal': 510,
        'maxMoves': 4,
        'shinyOdds': 8192,
        'ppUpMaxFraction': 1.6,   # max PP = base * 8/5
        'ppUpStages': 3,          # max PP Ups per move
    }

    # Weather mechanics: type boosts, DOT, immunities
    output['weatherMechanics'] = {
        'rain': {
            'typeBoosts': {'11': 1.5},    # Water
            'typeWeakens': {'10': 0.5},   # Fire
        },
        'sun': {
            'typeBoosts': {'10': 1.5},    # Fire
            'typeWeakens': {'11': 0.5},   # Water
        },
        'sandstorm': {
            'damagePerTurn': 0.0625,      # 1/16 max HP
            'immuneTypeIds': [5, 6, 9],   # Ground, Rock, Steel
        },
        'hail': {
            'damagePerTurn': 0.0625,      # 1/16 max HP
            'immuneTypeIds': [15],        # Ice
        },
    }

    # Write JSON
    out_path = os.path.join('..', 'pokedata3g', 'src', 'data.json')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(output, f, separators=(',', ':'), indent=2)

    size = os.path.getsize(out_path)
    print(f'Wrote {size:,} bytes ({size/1024:.1f} KB) to {out_path}')

    # Copy sprite files into module
    sprite_dest = os.path.join('..', 'pokedata3g', 'sprites')
    if os.path.exists(sprite_dest):
        shutil.rmtree(sprite_dest)
    shutil.copytree(os.path.join('assets', 'sprites'), sprite_dest)
    sprite_count = sum(len(files) for _, _, files in os.walk(sprite_dest))
    print(f'Copied {sprite_count} sprite files to {sprite_dest}/')


if __name__ == '__main__':
    generate()
