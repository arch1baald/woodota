from typing import List, Dict

import dota
from utils import convert_binary_mask_to_intervals, merge_close_intervals, has_intersection
from settings import HP_RATE_THRESHOLD, MAX_HP_THRESHOLD, MERGE_GAP


def find_hp_decreasing_intervals(player: 'dota.MatchPlayer') -> List[Dict]:
    """Signal with intervals where player has negative hp diff"""
    binary_mask = player.sdhp < HP_RATE_THRESHOLD
    intervals = convert_binary_mask_to_intervals(binary_mask)
    intervals = merge_close_intervals(intervals, MERGE_GAP)
    return intervals


def find_low_hp_intervals(player: 'dota.MatchPlayer') -> List[Dict]:
    """Signal with intervals where player has low hp"""
    series = player.hp / player.max_hp
    binary_mask = series < MAX_HP_THRESHOLD
    intervals = convert_binary_mask_to_intervals(binary_mask)
    intervals = merge_close_intervals(intervals, MERGE_GAP)
    return intervals


def find_low_and_decreasing_hp_intervals(player: 'dota.MatchPlayer') -> List[Dict]:
    """Signal with intervals where player has negative hp diff and has low hp"""
    hp_decreasing_intervals = find_hp_decreasing_intervals(player)
    low_hp_intervals = find_low_hp_intervals(player)
    low_and_decreasing_hp_intervals = []
    for hp_decreasing_interval in hp_decreasing_intervals:
        for low_hp_interval in low_hp_intervals:
            if hp_decreasing_interval['end'] < low_hp_interval['start']:
                break
            if has_intersection(hp_decreasing_interval, low_hp_interval):
                low_and_decreasing_hp_intervals.append(hp_decreasing_interval)
    return low_and_decreasing_hp_intervals


def find_attacks(player: 'dota.MatchPlayer') -> List[Dict]:
    """Intervals where player was attecked"""
    match = player.match
    intervals = find_low_and_decreasing_hp_intervals(player)
    for interval in intervals:
        is_dead = player.deaths.t(interval['start'], interval['end']).shape[0]
        if is_dead:
            interval['target_dead'] = True
        else:
            interval['target_dead'] = False

        df_input_damage = player.hero_damage_in.t(interval['start'], interval['end'])
        attacker_heroes = df_input_damage['sourcename'].unique()
        converted_to_players = []
        for hero_name in attacker_heroes:
            hero_player = match.get_player(hero_name)
            converted_to_players.append(hero_player)
        interval['attacker_heroes'] = converted_to_players
    return intervals
