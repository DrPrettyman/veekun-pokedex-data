#!/usr/bin/env python3
"""Generate compact Pokemon JSON for the pokedata3g npm module."""

import json
import os
import shutil

os.chdir(os.path.dirname(os.path.abspath(__file__)))

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


def compact_form_data(form_dict, transform=None):
    """Flatten single-form data; keep dict with string keys for multi-form."""
    if len(form_dict) == 1 and 0 in form_dict:
        val = form_dict[0]
        return transform(val) if transform else val
    result = {}
    for fk, v in form_dict.items():
        result[str(fk)] = transform(v) if transform else v
    return result


def generate():
    pokemon = coagulate.Pokemon()

    output = {"pokemon": {}}

    for d in pokemon._dict.values():
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

        output['pokemon'][str(d['id'])] = entry

    # Write JSON
    out_path = os.path.join('pokedata3g', 'src', 'data.json')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(output, f, separators=(',', ':'))

    size = os.path.getsize(out_path)
    print(f'Wrote {size:,} bytes ({size/1024:.1f} KB) to {out_path}')

    # Copy sprite files into module
    sprite_dest = os.path.join('pokedata3g', 'sprites')
    if os.path.exists(sprite_dest):
        shutil.rmtree(sprite_dest)
    shutil.copytree('sprites', sprite_dest)
    sprite_count = sum(len(files) for _, _, files in os.walk(sprite_dest))
    print(f'Copied {sprite_count} sprite files to {sprite_dest}/')


if __name__ == '__main__':
    generate()
