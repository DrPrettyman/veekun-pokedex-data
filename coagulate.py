import os
import pandas as pd


def _clean_strings(df: pd.DataFrame) -> pd.DataFrame:
    """Clean up whitespace in all string columns."""
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].str.replace(r'\s+', ' ', regex=True)
    return df


def _lookup(csv_path, id_col, name_col, lang_col='local_language_id'):
    """Build a simple {id: name} dict from a localized CSV, English only."""
    df = pd.read_csv(csv_path)
    df = df[df[lang_col] == 9]
    return dict(zip(df[id_col], df[name_col]))


EVOLUTION_TRIGGERS = _lookup('csv/evolution_trigger_prose.csv', 'evolution_trigger_id', 'name')
EGG_GROUPS = _lookup('csv/egg_group_prose.csv', 'egg_group_id', 'name')
MOVE_AILMENTS = _lookup('csv/move_meta_ailment_names.csv', 'move_meta_ailment_id', 'name')
MOVE_CATEGORIES = _lookup('csv/move_meta_category_prose.csv', 'move_meta_category_id', 'description')
MOVE_DAMAGE_CLASSES = _lookup('csv/move_damage_class_prose.csv', 'move_damage_class_id', 'name')
GROWTH_RATES = _lookup('csv/growth_rate_prose.csv', 'growth_rate_id', 'name')
POKEMON_COLORS = _lookup('csv/pokemon_color_names.csv', 'pokemon_color_id', 'name')
POKEMON_HABITATS = _lookup('csv/pokemon_habitat_names.csv', 'pokemon_habitat_id', 'name')
POKEMON_SHAPES = _lookup('csv/pokemon_shape_prose.csv', 'pokemon_shape_id', 'name')
MOVE_METHODS = dict(zip(
    pd.read_csv('csv/pokemon_move_methods.csv')['id'],
    pd.read_csv('csv/pokemon_move_methods.csv')['identifier'],
))
BERRY_FIRMNESS = _lookup('csv/berry_firmness_names.csv', 'berry_firmness_id', 'name')
CONTEST_FLAVORS = {
    row['contest_type_id']: row['flavor']
    for _, row in pd.read_csv('csv/contest_type_names.csv')[
        lambda d: d['local_language_id'] == 9
    ].iterrows()
}


class Abilities:
    def __init__(self):
        df = pd.read_csv('csv/abilities.csv')
        df = df[(df['generation_id'] <= 3) & (df['is_main_series'] == 1)].drop(columns=['generation_id', 'is_main_series'])

        names = pd.read_csv('csv/ability_names.csv')
        names = names[names['local_language_id']==9].drop(columns=['id', 'local_language_id']).dropna()

        df = pd.merge(
            left=df,
            right=names,
            how='left',
            left_on='id',
            right_on='ability_id'
        ).drop(columns=['ability_id'])

        flavor_text = pd.read_csv('csv/ability_flavor_text.csv')
        flavor_text = flavor_text[
            (flavor_text['ability_id'].isin(df['id']))
            & (flavor_text['language_id'] == 9)
            & (flavor_text['version_group_id'].isin((5,6,7)))
        ].drop(columns = ['language_id'])
        flavor_text = flavor_text.sort_values(
            'version_group_id', ascending=False
            ).drop_duplicates(
                subset=['ability_id'], keep='first'
            ).drop(columns=['version_group_id', 'id'])

        df = pd.merge(
            left=df,
            right=flavor_text,
            how='left',
            left_on='id',
            right_on='ability_id'
        ).drop(columns=['ability_id'])

        prose = pd.read_csv('csv/ability_prose.csv')
        prose = prose[prose['local_language_id']==9].drop(columns=['local_language_id', 'id']).dropna()

        df = pd.merge(
            left=df,
            right=prose,
            how='left',
            left_on='id',
            right_on='ability_id'
        ).drop(columns=['ability_id'])

        # Get Gen 3 ability change notes from ability_changelog
        abl_changelog = pd.read_csv('csv/ability_changelog.csv')
        abl_changelog = abl_changelog[abl_changelog['changed_in_version_group_id'] > 7]
        abl_changelog_prose = pd.read_csv('csv/ability_changelog_prose.csv')
        abl_changelog_prose = abl_changelog_prose[abl_changelog_prose['local_language_id']==9]
        abl_changelog = pd.merge(
            abl_changelog, abl_changelog_prose[['ability_changelog_id', 'effect']],
            left_on='id', right_on='ability_changelog_id'
        ).rename(columns={'effect': 'note'}).sort_values('changed_in_version_group_id')
        ability_notes = abl_changelog.groupby('ability_id')['note'].apply(list).to_dict()

        df = _clean_strings(df)

        self._df = df

        self._dict = df.set_index('id', drop=False).to_dict(orient='index')
        for ability_id in self._dict:
            self._dict[ability_id]['effect_notes'] = ability_notes.get(ability_id, [])
        self._name_id_map = {d['name']: d['id'] for d in self._dict.values()}
        self._identifier_id_map = {d['identifier']: d['id'] for d in self._dict.values()}
    
    def __getitem__(self, index: str | int):
        if isinstance(index, int):
            return self._dict.get(index)
        if isinstance(index, str):
            if index in self._name_id_map:
                return self._dict[self._name_id_map[index]]
            elif index in self._identifier_id_map:
                return self._dict[self._identifier_id_map[index]]
            else:
                return None
        raise ValueError(f'Invalid index type: {type(index)}')
    
    
class Natures:
    def __init__(self):
        df = pd.read_csv('csv/natures.csv').drop(columns=['game_index'])

        names = pd.read_csv('csv/nature_names.csv')
        names = names[names['local_language_id']==9].drop(columns=['id', 'local_language_id']).dropna()

        df = pd.merge(
            left=df,
            right=names,
            how='left',
            left_on='id',
            right_on='nature_id'
        ).drop(columns=['nature_id'])

        # Get stat names for increased/decreased stats
        stat_names = pd.read_csv('csv/stat_names.csv')
        stat_names = stat_names[stat_names['local_language_id']==9][['stat_id', 'name']]

        df = pd.merge(
            left=df,
            right=stat_names.rename(columns={'name': 'increased_stat'}),
            how='left',
            left_on='increased_stat_id',
            right_on='stat_id'
        ).drop(columns=['stat_id'])

        df = pd.merge(
            left=df,
            right=stat_names.rename(columns={'name': 'decreased_stat'}),
            how='left',
            left_on='decreased_stat_id',
            right_on='stat_id'
        ).drop(columns=['stat_id'])

        df = _clean_strings(df)

        self._df = df

        self._dict = df.set_index('id', drop=False).to_dict(orient='index')
        self._name_id_map = {d['name']: d['id'] for d in self._dict.values()}
        self._identifier_id_map = {d['identifier']: d['id'] for d in self._dict.values()}

    def __getitem__(self, index: str | int):
        if isinstance(index, int):
            return self._dict.get(index)
        if isinstance(index, str):
            if index in self._name_id_map:
                return self._dict[self._name_id_map[index]]
            elif index in self._identifier_id_map:
                return self._dict[self._identifier_id_map[index]]
            else:
                return None
        raise ValueError(f'Invalid index type: {type(index)}')


class Items:
    def __init__(self):
        # Get items that exist in Gen 3
        game_indices = pd.read_csv('csv/item_game_indices.csv')
        gen3_item_ids = game_indices[game_indices['generation_id'] <= 3]['item_id'].unique()

        df = pd.read_csv('csv/items.csv')
        df = df[df['id'].isin(gen3_item_ids)].drop(columns=['fling_power', 'fling_effect_id'])

        # Get category and pocket info
        categories = pd.read_csv('csv/item_categories.csv')[['id', 'pocket_id']]
        category_names = pd.read_csv('csv/item_category_prose.csv')
        category_names = category_names[category_names['local_language_id']==9][['item_category_id', 'name']]
        category_names = category_names.rename(columns={'name': 'category'})

        pocket_names = pd.read_csv('csv/item_pocket_names.csv')
        pocket_names = pocket_names[pocket_names['local_language_id']==9][['item_pocket_id', 'name']]
        pocket_names = pocket_names.rename(columns={'name': 'pocket'})

        df = pd.merge(left=df, right=categories, how='left', left_on='category_id', right_on='id', suffixes=('', '_cat'))
        df = df.drop(columns=['id_cat'])
        df = pd.merge(left=df, right=category_names, how='left', left_on='category_id', right_on='item_category_id')
        df = df.drop(columns=['item_category_id'])
        df = pd.merge(left=df, right=pocket_names, how='left', left_on='pocket_id', right_on='item_pocket_id')
        df = df.drop(columns=['item_pocket_id'])

        names = pd.read_csv('csv/item_names.csv')
        names = names[names['local_language_id']==9].drop(columns=['id', 'local_language_id']).dropna()

        df = pd.merge(
            left=df,
            right=names,
            how='left',
            left_on='id',
            right_on='item_id'
        ).drop(columns=['item_id'])

        flavor_text = pd.read_csv('csv/item_flavor_text.csv')
        flavor_text = flavor_text[
            (flavor_text['item_id'].isin(df['id']))
            & (flavor_text['language_id'] == 9)
            & (flavor_text['version_group_id'].isin((5,6,7)))
        ].drop(columns=['language_id'])
        flavor_text = flavor_text.sort_values(
            'version_group_id', ascending=False
        ).drop_duplicates(
            subset=['item_id'], keep='first'
        ).drop(columns=['version_group_id', 'id'])

        df = pd.merge(
            left=df,
            right=flavor_text,
            how='left',
            left_on='id',
            right_on='item_id'
        ).drop(columns=['item_id'])

        prose = pd.read_csv('csv/item_prose.csv')
        prose = prose[prose['local_language_id']==9].drop(columns=['local_language_id', 'id']).dropna()

        df = pd.merge(
            left=df,
            right=prose,
            how='left',
            left_on='id',
            right_on='item_id'
        ).drop(columns=['item_id'])

        # Get flag_ids for each item (as a list)
        flag_map = pd.read_csv('csv/item_flag_map.csv')
        flag_map = flag_map[flag_map['item_id'].isin(df['id'])]
        item_flags = flag_map.groupby('item_id')['item_flag_id'].apply(list).to_dict()

        df = _clean_strings(df)

        self._df = df

        self._dict = df.set_index('id', drop=False).to_dict(orient='index')
        # Add flag_ids list to each item
        for item_id in self._dict:
            self._dict[item_id]['flag_ids'] = item_flags.get(item_id, [])

        self._name_id_map = {d['name']: d['id'] for d in self._dict.values()}
        self._identifier_id_map = {d['identifier']: d['id'] for d in self._dict.values()}

    def __getitem__(self, index: str | int):
        if isinstance(index, int):
            return self._dict.get(index)
        if isinstance(index, str):
            if index in self._name_id_map:
                return self._dict[self._name_id_map[index]]
            elif index in self._identifier_id_map:
                return self._dict[self._identifier_id_map[index]]
            else:
                return None
        raise ValueError(f'Invalid index type: {type(index)}')


class ItemFlags:
    def __init__(self):
        df = pd.read_csv('csv/item_flags.csv')

        prose = pd.read_csv('csv/item_flag_prose.csv')
        prose = prose[prose['local_language_id']==9][['item_flag_id', 'name', 'description']]

        df = pd.merge(
            left=df,
            right=prose,
            how='left',
            left_on='id',
            right_on='item_flag_id'
        ).drop(columns=['item_flag_id'])

        df = _clean_strings(df)

        self._df = df

        self._dict = df.set_index('id', drop=False).to_dict(orient='index')
        self._name_id_map = {d['name']: d['id'] for d in self._dict.values()}
        self._identifier_id_map = {d['identifier']: d['id'] for d in self._dict.values()}

    def __getitem__(self, index: str | int):
        if isinstance(index, int):
            return self._dict.get(index)
        if isinstance(index, str):
            if index in self._name_id_map:
                return self._dict[self._name_id_map[index]]
            elif index in self._identifier_id_map:
                return self._dict[self._identifier_id_map[index]]
            else:
                return None
        raise ValueError(f'Invalid index type: {type(index)}')


class Types:
    def __init__(self):
        df = pd.read_csv('csv/types.csv')
        df = df[(df['generation_id'] <= 3) & (df['id'] < 10000)].drop(columns=['generation_id'])
        # Convert damage_class_id from float to nullable int
        df['damage_class_id'] = df['damage_class_id'].astype('Int64')

        names = pd.read_csv('csv/type_names.csv')
        names = names[names['local_language_id']==9][['type_id', 'name']]

        df = pd.merge(
            left=df,
            right=names,
            how='left',
            left_on='id',
            right_on='type_id'
        ).drop(columns=['type_id'])

        # Build efficacy dict for each type (damage this type deals to other types)
        efficacy = pd.read_csv('csv/type_efficacy.csv')
        # Filter to only non-100 damage factors (interesting ones)
        efficacy = efficacy[efficacy['damage_factor'] != 100]
        # Convert damage_factor to multiplier (0, 0.5, 2)
        efficacy['multiplier'] = efficacy['damage_factor'] / 100
        type_efficacy = efficacy.groupby('damage_type_id')[['target_type_id', 'multiplier']].apply(
            lambda g: dict(zip(g['target_type_id'], g['multiplier'])), include_groups=False
        ).to_dict()

        df = _clean_strings(df)

        self._df = df

        self._dict = df.set_index('id', drop=False).to_dict(orient='index')
        # Add efficacy dict to each type
        for type_id in self._dict:
            self._dict[type_id]['efficacy'] = type_efficacy.get(type_id, {})

        self._name_id_map = {d['name']: d['id'] for d in self._dict.values()}
        self._identifier_id_map = {d['identifier']: d['id'] for d in self._dict.values()}

    def __getitem__(self, index: str | int):
        if isinstance(index, int):
            return self._dict.get(index)
        if isinstance(index, str):
            if index in self._name_id_map:
                return self._dict[self._name_id_map[index]]
            elif index in self._identifier_id_map:
                return self._dict[self._identifier_id_map[index]]
            else:
                return None
        raise ValueError(f'Invalid index type: {type(index)}')


class MoveFlags:
    def __init__(self):
        df = pd.read_csv('csv/move_flags.csv')

        prose = pd.read_csv('csv/move_flag_prose.csv')
        prose = prose[prose['local_language_id']==9][['move_flag_id', 'name', 'description']]

        df = pd.merge(
            left=df,
            right=prose,
            how='left',
            left_on='id',
            right_on='move_flag_id'
        ).drop(columns=['move_flag_id'])

        df = _clean_strings(df)

        self._df = df

        self._dict = df.set_index('id', drop=False).to_dict(orient='index')
        self._name_id_map = {d['name']: d['id'] for d in self._dict.values()}
        self._identifier_id_map = {d['identifier']: d['id'] for d in self._dict.values()}

    def __getitem__(self, index: str | int):
        if isinstance(index, int):
            return self._dict.get(index)
        if isinstance(index, str):
            if index in self._name_id_map:
                return self._dict[self._name_id_map[index]]
            elif index in self._identifier_id_map:
                return self._dict[self._identifier_id_map[index]]
            else:
                return None
        raise ValueError(f'Invalid index type: {type(index)}')


class Moves:
    def __init__(self):
        df = pd.read_csv('csv/moves.csv')
        df = df[(df['generation_id'] <= 3) & (df['type_id'] < 10000)].drop(columns=[
            'generation_id', 'contest_type_id', 'contest_effect_id', 'super_contest_effect_id'
        ])

        # Apply move_changelog to revert post-Gen3 changes
        # Changelog stores the OLD value before each change; we want the
        # earliest post-Gen3 entry (lowest changed_in_version_group_id > 7)
        changelog = pd.read_csv('csv/move_changelog.csv')
        changelog = changelog[
            (changelog['move_id'].isin(df['id']))
            & (changelog['changed_in_version_group_id'] > 7)
        ].sort_values('changed_in_version_group_id')
        changelog_fields = ['type_id', 'power', 'pp', 'accuracy', 'priority',
                           'target_id', 'effect_id', 'effect_chance']
        for move_id, group in changelog.groupby('move_id'):
            for field in changelog_fields:
                # Find the earliest change for this field
                changed = group[group[field].notna()]
                if not changed.empty:
                    old_value = changed.iloc[0][field]
                    df.loc[df['id'] == move_id, field] = old_value

        # Convert int columns (some may have NaN which pandas reads as float)
        for col in ['power', 'pp', 'accuracy', 'effect_chance']:
            df[col] = df[col].astype('Int64')

        # Get English names
        names = pd.read_csv('csv/move_names.csv')
        names = names[names['local_language_id']==9].drop(columns=['id', 'local_language_id']).dropna()

        df = pd.merge(
            left=df,
            right=names,
            how='left',
            left_on='id',
            right_on='move_id'
        ).drop(columns=['move_id'])

        # Get flavor text (highest version_group_id from Gen 3)
        flavor_text = pd.read_csv('csv/move_flavor_text.csv')
        flavor_text = flavor_text[
            (flavor_text['move_id'].isin(df['id']))
            & (flavor_text['language_id'] == 9)
            & (flavor_text['version_group_id'].isin((5,6,7)))
        ].drop(columns=['language_id'])
        flavor_text = flavor_text.sort_values(
            'version_group_id', ascending=False
        ).drop_duplicates(
            subset=['move_id'], keep='first'
        ).drop(columns=['version_group_id', 'id'])

        df = pd.merge(
            left=df,
            right=flavor_text,
            how='left',
            left_on='id',
            right_on='move_id'
        ).drop(columns=['move_id'])

        # Get effect prose (short_effect and effect)
        effect_prose = pd.read_csv('csv/move_effect_prose.csv')
        effect_prose = effect_prose[effect_prose['local_language_id']==9][['move_effect_id', 'short_effect', 'effect']]

        df = pd.merge(
            left=df,
            right=effect_prose,
            how='left',
            left_on='effect_id',
            right_on='move_effect_id'
        ).drop(columns=['move_effect_id'])

        # Get Gen 3 effect change notes from move_effect_changelog
        # These are errata describing how the move behaved differently in Gen 3
        eff_changelog = pd.read_csv('csv/move_effect_changelog.csv')
        eff_changelog = eff_changelog[eff_changelog['changed_in_version_group_id'] > 7]
        eff_changelog_prose = pd.read_csv('csv/move_effect_changelog_prose.csv')
        eff_changelog_prose = eff_changelog_prose[eff_changelog_prose['local_language_id']==9]
        eff_changelog = pd.merge(
            eff_changelog, eff_changelog_prose[['move_effect_changelog_id', 'effect']],
            left_on='id', right_on='move_effect_changelog_id'
        ).rename(columns={'effect': 'note'}).sort_values('changed_in_version_group_id')
        # For each effect_id, collect all post-Gen3 change notes
        effect_notes = eff_changelog.groupby('effect_id')['note'].apply(list).to_dict()

        # Get target name
        target_prose = pd.read_csv('csv/move_target_prose.csv')
        target_prose = target_prose[target_prose['local_language_id']==9][['move_target_id', 'name', 'description']]
        target_prose = target_prose.rename(columns={'name': 'target', 'description': 'target_description'})

        df = pd.merge(
            left=df,
            right=target_prose,
            how='left',
            left_on='target_id',
            right_on='move_target_id'
        ).drop(columns=['move_target_id'])

        # Get move meta (battle mechanics)
        meta = pd.read_csv('csv/move_meta.csv').drop(columns=['id'])
        # Convert int columns in meta
        for col in ['meta_category_id', 'meta_ailment_id', 'min_hits', 'max_hits', 'min_turns', 'max_turns',
                    'drain', 'healing', 'crit_rate', 'ailment_chance', 'flinch_chance', 'stat_chance']:
            meta[col] = meta[col].astype('Int64')

        df = pd.merge(
            left=df,
            right=meta,
            how='left',
            left_on='id',
            right_on='move_id'
        ).drop(columns=['move_id'])

        # Rename meta columns for clarity
        df = df.rename(columns={
            'meta_category_id': 'category_id',
            'meta_ailment_id': 'ailment_id'
        })

        # Get flag_ids for each move (as a list)
        flag_map = pd.read_csv('csv/move_flag_map.csv')
        flag_map = flag_map[flag_map['move_id'].isin(df['id'])]
        move_flags = flag_map.groupby('move_id')['move_flag_id'].apply(list).to_dict()

        # Get stat_changes for each move (as a list of {stat_id, change})
        stat_changes = pd.read_csv('csv/move_meta_stat_changes.csv').drop(columns=['id'])
        stat_changes = stat_changes[stat_changes['move_id'].isin(df['id'])]
        move_stat_changes = stat_changes.groupby('move_id')[['stat_id', 'change']].apply(
            lambda g: [{'stat_id': int(r['stat_id']), 'change': int(r['change'])} for _, r in g.iterrows()],
            include_groups=False
        ).to_dict()

        df = _clean_strings(df)

        self._df = df

        self._dict = df.set_index('id', drop=False).to_dict(orient='index')
        # Add flag_ids and stat_changes to each move
        for move_id in self._dict:
            self._dict[move_id]['flag_ids'] = move_flags.get(move_id, [])
            self._dict[move_id]['stat_changes'] = move_stat_changes.get(move_id, [])
            self._dict[move_id]['effect_notes'] = effect_notes.get(self._dict[move_id]['effect_id'], [])

        self._name_id_map = {d['name']: d['id'] for d in self._dict.values()}
        self._identifier_id_map = {d['identifier']: d['id'] for d in self._dict.values()}

    def __getitem__(self, index: str | int):
        if isinstance(index, int):
            return self._dict.get(index)
        if isinstance(index, str):
            if index in self._name_id_map:
                return self._dict[self._name_id_map[index]]
            elif index in self._identifier_id_map:
                return self._dict[self._identifier_id_map[index]]
            else:
                return None
        raise ValueError(f'Invalid index type: {type(index)}')


class Stats:
    def __init__(self):
        df = pd.read_csv('csv/stats.csv')
        # Convert nullable int columns
        df['damage_class_id'] = df['damage_class_id'].astype('Int64')
        df['game_index'] = df['game_index'].astype('Int64')
        df['is_battle_only'] = df['is_battle_only'].astype(bool)

        names = pd.read_csv('csv/stat_names.csv')
        names = names[names['local_language_id']==9][['stat_id', 'name']]

        df = pd.merge(
            left=df,
            right=names,
            how='left',
            left_on='id',
            right_on='stat_id'
        ).drop(columns=['stat_id'])

        df = _clean_strings(df)

        self._df = df

        self._dict = df.set_index('id', drop=False).to_dict(orient='index')
        self._name_id_map = {d['name']: d['id'] for d in self._dict.values()}
        self._identifier_id_map = {d['identifier']: d['id'] for d in self._dict.values()}

    def __getitem__(self, index: str | int):
        if isinstance(index, int):
            return self._dict.get(index)
        if isinstance(index, str):
            if index in self._name_id_map:
                return self._dict[self._name_id_map[index]]
            elif index in self._identifier_id_map:
                return self._dict[self._identifier_id_map[index]]
            else:
                return None
        raise ValueError(f'Invalid index type: {type(index)}')


class Pokemon:
    def __init__(self):
        # Load species first to filter to Gen 3
        species = pd.read_csv('csv/pokemon_species.csv')
        species = species[species['generation_id'] <= 3].drop(columns=['generation_id', 'conquest_order'])

        # Convert int columns
        for col in ['evolves_from_species_id', 'color_id', 'shape_id', 'habitat_id']:
            species[col] = species[col].astype('Int64')
        species['is_baby'] = species['is_baby'].astype(bool)
        species['has_gender_differences'] = species['has_gender_differences'].astype(bool)
        species['forms_switchable'] = species['forms_switchable'].astype(bool)

        # Load ALL pokemon rows for Gen 3 species (including alternate forms)
        all_pokemon = pd.read_csv('csv/pokemon.csv')
        all_pokemon = all_pokemon[all_pokemon['species_id'].isin(species['id'])]

        # Load forms and filter to Gen 3 (introduced_in_version_group_id <= 7)
        forms_df = pd.read_csv('csv/pokemon_forms.csv')
        forms_df = forms_df[
            (forms_df['pokemon_id'].isin(all_pokemon['id']))
            & (forms_df['introduced_in_version_group_id'] <= 7)
        ].sort_values(['pokemon_id', 'form_order'])

        # Gen 3 pokemon_ids = those with Gen 3 forms
        gen3_pokemon_ids = set(forms_df['pokemon_id'].unique())

        # Get form names
        form_names_df = pd.read_csv('csv/pokemon_form_names.csv')
        form_names_df = form_names_df[form_names_df['local_language_id'] == 9]
        form_name_map = dict(zip(form_names_df['pokemon_form_id'], form_names_df['form_name']))

        # Map pokemon_id -> species_id for all pokemon
        pid_to_sid = dict(zip(all_pokemon['id'], all_pokemon['species_id']))

        # Build per-species form metadata
        forms_df = forms_df.copy()
        forms_df['species_id'] = forms_df['pokemon_id'].map(pid_to_sid)
        species_form_data = {}
        for sid, grp in forms_df.groupby('species_id'):
            form_list = []
            for _, row in grp.iterrows():
                form_list.append({
                    'pokemon_form_id': int(row['id']),
                    'pokemon_id': int(row['pokemon_id']),
                    'identifier': row['identifier'],
                    'form_identifier': row['form_identifier'] if pd.notna(row['form_identifier']) else None,
                    'is_battle_only': bool(row['is_battle_only']),
                })
            species_form_data[sid] = form_list

        # Build default-form df for species-level data (one row per species)
        default_pokemon = all_pokemon[
            all_pokemon['is_default'] == 1
        ].drop(columns=['order', 'is_default'])

        # Merge species data into default pokemon
        df = pd.merge(
            left=default_pokemon,
            right=species.drop(columns=['identifier', 'order']),
            how='left',
            left_on='species_id',
            right_on='id',
            suffixes=('', '_species')
        ).drop(columns=['id_species'])

        # Get English names and genus
        names = pd.read_csv('csv/pokemon_species_names.csv')
        names = names[names['local_language_id']==9][['pokemon_species_id', 'name', 'genus']]

        df = pd.merge(
            left=df,
            right=names,
            how='left',
            left_on='species_id',
            right_on='pokemon_species_id'
        ).drop(columns=['pokemon_species_id'])

        # --- Form-varying data: load for ALL Gen 3 pokemon_ids ---

        # Types
        types_df = pd.read_csv('csv/pokemon_types.csv')
        types_df = types_df[types_df['pokemon_id'].isin(gen3_pokemon_ids)].sort_values(['pokemon_id', 'slot'])
        pokemon_types = types_df.groupby('pokemon_id')['type_id'].apply(list).to_dict()

        # Stats
        stats_df = pd.read_csv('csv/pokemon_stats.csv')
        stats_df = stats_df[stats_df['pokemon_id'].isin(gen3_pokemon_ids)]
        pokemon_stats = stats_df.groupby('pokemon_id')[['stat_id', 'base_stat']].apply(
            lambda g: {int(r['stat_id']): int(r['base_stat']) for _, r in g.iterrows()},
            include_groups=False
        ).to_dict()

        # EV yields
        pokemon_evs = stats_df.groupby('pokemon_id')[['stat_id', 'effort']].apply(
            lambda g: {int(r['stat_id']): int(r['effort']) for _, r in g.iterrows() if r['effort'] > 0},
            include_groups=False
        ).to_dict()

        # Moves for ALL Gen 3 pokemon_ids
        moves_df = pd.read_csv('csv/pokemon_moves.csv')
        moves_df = moves_df[
            (moves_df['pokemon_id'].isin(gen3_pokemon_ids))
            & (moves_df['version_group_id'].isin((5, 6, 7)))
        ].drop(columns=['id', 'order'])
        moves_df = moves_df.sort_values('version_group_id', ascending=False).drop_duplicates(
            subset=['pokemon_id', 'move_id', 'pokemon_move_method_id', 'level'], keep='first'
        ).drop(columns=['version_group_id'])

        # Level-up moves: list of (move_id, level) tuples
        level_df = moves_df[moves_df['pokemon_move_method_id'] == 1]
        pokemon_level_moves = level_df.groupby('pokemon_id')[['move_id', 'level']].apply(
            lambda g: [(int(r['move_id']), int(r['level'])) for _, r in g.iterrows()],
            include_groups=False
        ).to_dict()

        # Teachable moves (tutor + machine): list of move_ids
        teach_df = moves_df[moves_df['pokemon_move_method_id'].isin([3, 4])]
        pokemon_teachable_moves = teach_df.groupby('pokemon_id')['move_id'].apply(
            lambda g: sorted(int(x) for x in g.unique())
        ).to_dict()

        # Egg moves: list of move_ids
        egg_df = moves_df[moves_df['pokemon_move_method_id'] == 2]
        pokemon_egg_moves = egg_df.groupby('pokemon_id')['move_id'].apply(
            lambda g: sorted(int(x) for x in g.unique())
        ).to_dict()

        # --- Species-level data (not form-varying) ---

        # Abilities (use default pokemon_id)
        abilities_df = pd.read_csv('csv/pokemon_abilities.csv')
        abilities_df = abilities_df[abilities_df['pokemon_id'].isin(df['id'])].sort_values(['pokemon_id', 'slot'])
        pokemon_abilities = abilities_df.groupby('pokemon_id')[['ability_id', 'is_hidden', 'slot']].apply(
            lambda g: [{'ability_id': int(r['ability_id']), 'is_hidden': bool(r['is_hidden']), 'slot': int(r['slot'])}
                      for _, r in g.iterrows()],
            include_groups=False
        ).to_dict()

        # Egg groups
        egg_groups_df = pd.read_csv('csv/pokemon_egg_groups.csv')
        egg_groups_df = egg_groups_df[egg_groups_df['species_id'].isin(df['species_id'])]
        species_egg_groups = egg_groups_df.groupby('species_id')['egg_group_id'].apply(list).to_dict()

        # Flavor text
        flavor_df = pd.read_csv('csv/pokemon_species_flavor_text.csv')
        flavor_df = flavor_df[
            (flavor_df['species_id'].isin(df['species_id']))
            & (flavor_df['language_id'] == 9)
            & (flavor_df['version_id'].isin(range(7, 12)))
        ].drop(columns=['language_id'])
        flavor_df = flavor_df.sort_values(
            'version_id', ascending=False
        ).drop_duplicates(
            subset=['species_id'], keep='first'
        ).drop(columns=['version_id', 'id'])

        df = pd.merge(
            left=df,
            right=flavor_df,
            how='left',
            left_on='species_id',
            right_on='species_id'
        )

        # Wild held items (use default pokemon_id)
        held_items_df = pd.read_csv('csv/pokemon_items.csv')
        held_items_df = held_items_df[
            (held_items_df['pokemon_id'].isin(df['id']))
            & (held_items_df['version_id'].isin(range(7, 12)))
        ].drop(columns=['id'])
        held_items_df = held_items_df.sort_values('version_id', ascending=False).drop_duplicates(
            subset=['pokemon_id', 'item_id'], keep='first'
        ).drop(columns=['version_id'])
        pokemon_held_items = held_items_df.groupby('pokemon_id')[['item_id', 'rarity']].apply(
            lambda g: [{'item_id': int(r['item_id']), 'rarity': int(r['rarity'])} for _, r in g.iterrows()],
            include_groups=False
        ).to_dict()

        # Evolution data
        evo_df = pd.read_csv('csv/pokemon_evolution.csv')
        evo_df = evo_df[evo_df['evolved_species_id'].isin(df['species_id'])]
        evo_df = pd.merge(
            left=evo_df,
            right=species[['id', 'evolves_from_species_id']],
            how='left',
            left_on='evolved_species_id',
            right_on='id',
            suffixes=('', '_species')
        ).drop(columns=['id_species'])
        for col in ['trigger_item_id', 'minimum_level', 'gender_id', 'location_id', 'held_item_id',
                    'known_move_id', 'known_move_type_id', 'minimum_happiness', 'minimum_beauty',
                    'minimum_affection', 'relative_physical_stats', 'party_species_id', 'party_type_id',
                    'trade_species_id', 'evolves_from_species_id']:
            evo_df[col] = evo_df[col].astype('Int64')
        evo_df['needs_overworld_rain'] = evo_df['needs_overworld_rain'].astype(bool)
        evo_df['turn_upside_down'] = evo_df['turn_upside_down'].astype(bool)

        from collections import defaultdict
        species_evolutions = defaultdict(list)
        for _, row in evo_df.iterrows():
            if pd.isna(row['evolves_from_species_id']):
                continue
            evo_data = {
                'to_species_id': int(row['evolved_species_id']),
                'trigger_id': int(row['evolution_trigger_id']),
            }
            if pd.notna(row['minimum_level']): evo_data['minimum_level'] = int(row['minimum_level'])
            if pd.notna(row['trigger_item_id']): evo_data['trigger_item_id'] = int(row['trigger_item_id'])
            if pd.notna(row['held_item_id']): evo_data['held_item_id'] = int(row['held_item_id'])
            if pd.notna(row['known_move_id']): evo_data['known_move_id'] = int(row['known_move_id'])
            if pd.notna(row['minimum_happiness']): evo_data['minimum_happiness'] = int(row['minimum_happiness'])
            if pd.notna(row['minimum_beauty']): evo_data['minimum_beauty'] = int(row['minimum_beauty'])
            if pd.notna(row['time_of_day']) and row['time_of_day']: evo_data['time_of_day'] = row['time_of_day']
            if pd.notna(row['gender_id']): evo_data['gender_id'] = int(row['gender_id'])
            if pd.notna(row['location_id']): evo_data['location_id'] = int(row['location_id'])
            if pd.notna(row['trade_species_id']): evo_data['trade_species_id'] = int(row['trade_species_id'])
            species_evolutions[int(row['evolves_from_species_id'])].append(evo_data)

        df = _clean_strings(df)

        self._df = df

        # Helper: build form-keyed dict (1-indexed). If all forms share the
        # same value, collapse to {0: value}. For battle-only forms with no
        # data, inherit from the first non-battle-only form.
        def _normalize(v):
            if isinstance(v, list):
                return sorted(v)
            return v

        def _form_keyed(form_list, data_fn):
            per_form = {}
            default_data = None
            for form in form_list:
                if not form['is_battle_only']:
                    default_data = data_fn(form['pokemon_id'])
                    break
            for i, form in enumerate(form_list, 1):
                data = data_fn(form['pokemon_id'])
                if not data and form['is_battle_only'] and default_data is not None:
                    data = default_data
                per_form[i] = data
            vals = list(per_form.values())
            if all(_normalize(v) == _normalize(vals[0]) for v in vals[1:]):
                return {0: vals[0]}
            return per_form

        self._dict = df.set_index('id', drop=False).to_dict(orient='index')

        for pokemon_id in self._dict:
            d = self._dict[pokemon_id]
            species_id = d['species_id']
            form_list = species_form_data.get(species_id, [])

            if len(form_list) <= 1:
                # Single form (the vast majority)
                d['forms'] = [0]
                d['identifier'] = {0: d.pop('identifier')}
                d['form_identifier'] = {}
                d['form_name'] = {}
                d['type_ids'] = {0: pokemon_types.get(pokemon_id, [])}
                d['stats'] = {0: pokemon_stats.get(pokemon_id, {})}
                d['ev_yields'] = {0: pokemon_evs.get(pokemon_id, {})}
                d['level_moves'] = {0: pokemon_level_moves.get(pokemon_id, [])}
                d['teachable_moves'] = {0: pokemon_teachable_moves.get(pokemon_id, [])}
                d['egg_moves'] = {0: pokemon_egg_moves.get(pokemon_id, [])}
            else:
                # Multiple forms (1-indexed)
                d['forms'] = list(range(1, len(form_list) + 1))
                d.pop('identifier')
                d['identifier'] = {}
                d['form_identifier'] = {}
                d['form_name'] = {}
                for i, form in enumerate(form_list, 1):
                    d['identifier'][i] = form['identifier']
                    if form['form_identifier']:
                        d['form_identifier'][i] = form['form_identifier']
                    fn = form_name_map.get(form['pokemon_form_id'], '')
                    if fn:
                        d['form_name'][i] = fn
                d['type_ids'] = _form_keyed(form_list, lambda pid: pokemon_types.get(pid, []))
                d['stats'] = _form_keyed(form_list, lambda pid: pokemon_stats.get(pid, {}))
                d['ev_yields'] = _form_keyed(form_list, lambda pid: pokemon_evs.get(pid, {}))
                d['level_moves'] = _form_keyed(form_list, lambda pid: pokemon_level_moves.get(pid, []))
                d['teachable_moves'] = _form_keyed(form_list, lambda pid: pokemon_teachable_moves.get(pid, []))
                d['egg_moves'] = _form_keyed(form_list, lambda pid: pokemon_egg_moves.get(pid, []))

            # Sprites (form-varying, built from identifiers)
            sprite_base = 'sprites'
            def _sprite_path(sprite_type, ident):
                path = os.path.join(sprite_base, sprite_type, f'{ident}.png')
                return path if os.path.isfile(path) else None

            sprites = {}
            for sprite_type in ('front', 'back', 'front_shiny', 'back_shiny', 'icon'):
                form_sprites = {}
                for fi, ident in d['identifier'].items():
                    path = _sprite_path(sprite_type, ident)
                    if path:
                        form_sprites[fi] = path
                if form_sprites:
                    # Collapse to {0: path} if all forms have the same sprite
                    vals = list(form_sprites.values())
                    if len(form_sprites) == 1:
                        sprites[sprite_type] = vals[0]
                    else:
                        sprites[sprite_type] = form_sprites

            # Footprint is species-level (not form-varying)
            # Use base identifier (first non-form identifier, or species name)
            base_ident = d['identifier'].get(0, None)
            if base_ident is None:
                # Multi-form: use species-level name for footprint
                # e.g., 'deoxys' for deoxys-normal, 'castform' for castform, 'unown' for unown-a
                base_ident = d['name'].lower().replace(' ', '-').replace('.', '')
            fp_path = _sprite_path('footprint', base_ident)
            if fp_path:
                sprites['footprint'] = fp_path
            d['sprites'] = sprites

            # Species-level attributes (not form-varying)
            d['abilities'] = pokemon_abilities.get(pokemon_id, [])
            d['egg_group_ids'] = species_egg_groups.get(species_id, [])
            d['evolutions'] = species_evolutions.get(species_id, [])
            d['held_items'] = pokemon_held_items.get(pokemon_id, [])

        self._name_id_map = {d['name']: d['id'] for d in self._dict.values() if d.get('name')}
        # Map all form identifiers for lookup
        self._identifier_id_map = {}
        for d in self._dict.values():
            for ident in d['identifier'].values():
                self._identifier_id_map[ident] = d['id']
        self._species_id_map = {d['species_id']: d['id'] for d in self._dict.values()}

    def __getitem__(self, index: str | int):
        if isinstance(index, int):
            # Try pokemon_id first, then species_id
            if index in self._dict:
                return self._dict[index]
            elif index in self._species_id_map:
                return self._dict[self._species_id_map[index]]
            return None
        if isinstance(index, str):
            if index in self._name_id_map:
                return self._dict[self._name_id_map[index]]
            elif index in self._identifier_id_map:
                return self._dict[self._identifier_id_map[index]]
            else:
                return None
        raise ValueError(f'Invalid index type: {type(index)}')


class Machines:
    """TM/HM mappings for Gen 3. Keyed by machine_number (1-50 = TMs, 101-108 = HMs)."""
    def __init__(self):
        df = pd.read_csv('csv/machines.csv')
        df = df[df['version_group_id'].isin((5, 6, 7))].drop(columns=['id'])

        # Dedupe: keep highest version_group for each machine_number
        df = df.sort_values('version_group_id', ascending=False).drop_duplicates(
            subset=['machine_number'], keep='first'
        ).drop(columns=['version_group_id'])

        self._dict = {}
        for _, row in df.iterrows():
            num = int(row['machine_number'])
            if num <= 50:
                label = f'TM{num:02d}'
            else:
                label = f'HM{num - 100:02d}'
            self._dict[num] = {
                'machine_number': num,
                'label': label,
                'item_id': int(row['item_id']),
                'move_id': int(row['move_id']),
            }

        self._label_map = {d['label']: d['machine_number'] for d in self._dict.values()}

    def __getitem__(self, index: str | int):
        if isinstance(index, int):
            return self._dict.get(index)
        if isinstance(index, str):
            idx = index.upper()
            if idx in self._label_map:
                return self._dict[self._label_map[idx]]
            return None
        raise ValueError(f'Invalid index type: {type(index)}')

    def all(self):
        return list(self._dict.values())


class ExperienceTable:
    """XP required per level per growth rate. Lookup: table[growth_rate_id] -> {level: xp, ...}"""
    def __init__(self):
        df = pd.read_csv('csv/experience.csv').drop(columns=['id'])

        self._dict = {}
        for growth_rate_id, group in df.groupby('growth_rate_id'):
            self._dict[int(growth_rate_id)] = {
                int(row['level']): int(row['experience']) for _, row in group.iterrows()
            }

    def __getitem__(self, growth_rate_id: int):
        return self._dict.get(growth_rate_id)

    def xp_for_level(self, growth_rate_id: int, level: int):
        table = self._dict.get(growth_rate_id)
        if table:
            return table.get(level)
        return None


class Berries:
    """Gen 3 berries with firmness, flavors, and natural gift data."""
    def __init__(self):
        df = pd.read_csv('csv/berries.csv')
        # Berries 1-43 are Gen 3 (items 126-168)
        df = df[df['id'] <= 43]

        for col in ['natural_gift_power', 'natural_gift_type_id']:
            df[col] = df[col].astype('Int64')

        # Get item names (berries are items)
        item_names = pd.read_csv('csv/item_names.csv')
        item_names = item_names[item_names['local_language_id'] == 9][['item_id', 'name']]

        df = pd.merge(
            left=df,
            right=item_names,
            how='left',
            left_on='item_id',
            right_on='item_id'
        )

        # Get berry flavors (contest_type_id -> flavor intensity)
        flavors_df = pd.read_csv('csv/berry_flavors.csv').drop(columns=['id'])
        flavors_df = flavors_df[flavors_df['berry_id'].isin(df['id'])]

        # Map contest_type_id to flavor name and build dict per berry
        berry_flavors = {}
        for berry_id, group in flavors_df.groupby('berry_id'):
            berry_flavors[berry_id] = {
                CONTEST_FLAVORS[int(row['contest_type_id'])]: int(row['flavor'])
                for _, row in group.iterrows()
                if int(row['flavor']) > 0
            }

        df = _clean_strings(df)

        self._dict = df.set_index('id', drop=False).to_dict(orient='index')
        for berry_id in self._dict:
            self._dict[berry_id]['flavors'] = berry_flavors.get(berry_id, {})

        self._name_map = {d['name']: d['id'] for d in self._dict.values() if d.get('name')}

    def __getitem__(self, index: str | int):
        if isinstance(index, int):
            return self._dict.get(index)
        if isinstance(index, str):
            if index in self._name_map:
                return self._dict[self._name_map[index]]
            return None
        raise ValueError(f'Invalid index type: {type(index)}')

    def all(self):
        return list(self._dict.values())
