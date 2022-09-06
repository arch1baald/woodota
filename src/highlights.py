from typing import List, Dict

from dota import MatchPlayer
from utils import TimeSeries
from settings import HP_RATE_THRESHOLD, MAX_HP_THRESHOLD, MERGE_GAP


def convert_binary_mask_to_intervals(binary_mask: TimeSeries) -> List[Dict]:
    if binary_mask.empty:
        return []

    intervals = [dict()]
    prev_flag = False
    for time, flag in binary_mask.iteritems():
        last_interval = intervals[-1]
        if flag is True and prev_flag is False:
            last_interval['start'] = time
        if flag is False and prev_flag is True:
            last_interval['end'] = time
            intervals.append(dict())
        prev_flag = flag

    last_interval = intervals[-1]
    if not last_interval:
        intervals.pop()

    if 'start' in last_interval and 'end' not in last_interval:
        series_last_time = binary_mask.index[-1]
        if last_interval['start'] != series_last_time:
            last_interval['end'] = series_last_time
        else:
            intervals.pop()
    return intervals


def merge_close_intervals(intervals: List[Dict], gap: int) -> List[Dict]:
    """
    Merges intervals if difference between start and end is less or equal to gap
    """
    if len(intervals) < 2:
        return intervals

    intervals = sorted(intervals, key=lambda dct: (dct['start'], dct['end']))
    merged = []
    prev = intervals[0]
    for current in intervals[1:]:
        if current['start'] <= (prev['end'] + gap):
            prev = dict(
                start=prev['start'],
                end=max(current['end'], prev['end'])
            )
        else:
            merged.append(prev)
            prev = current
    if not merged or merged[-1] != prev:
        merged.append(prev)
    return merged


def has_intersection(interval1: Dict, interval2: Dict, gap: int = 0) -> bool:
    """By default gap = 0, checks for strict intersection"""
    merged = merge_close_intervals([interval1, interval2], gap)
    return len(merged) < 2


def find_hp_decreasing_intervals(player: MatchPlayer) -> List[Dict]:
    """Signal with intervals where player has negative hp diff"""
    binary_mask = player.sdhp < HP_RATE_THRESHOLD
    intervals = convert_binary_mask_to_intervals(binary_mask)
    intervals = merge_close_intervals(intervals, MERGE_GAP)
    return intervals


def find_low_hp_intervals(player: MatchPlayer) -> List[Dict]:
    """Signal with intervals where player has low hp"""
    series = player.hp / player.max_hp
    binary_mask = series < MAX_HP_THRESHOLD
    intervals = convert_binary_mask_to_intervals(binary_mask)
    intervals = merge_close_intervals(intervals, MERGE_GAP)
    return intervals


def find_low_and_decreasing_hp_intervals(player: MatchPlayer) -> List[Dict]:
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


def find_attacks(player: MatchPlayer) -> List[Dict]:
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
