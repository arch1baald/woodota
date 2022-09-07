import logging
import functools
import weakref
from typing import Any, List, Dict, Tuple

import requests
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_fixed
from loguru import logger


class DisableLogger:
    def __enter__(self):
        logging.disable(logging.CRITICAL)

    def __exit__(self, exception_type: Any, exception_value: Any, traceback: Any):
        logging.disable(logging.NOTSET)


class EmptyDebugLogger(logging.Logger):
    def debug(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def query_opendota(sql: str, **kwargs: dict) -> List[Dict]:
    query = sql.format(**kwargs)
    logger.debug(query)
    query = query.replace('\n', ' ').replace('\t', ' ')
    query = ' '.join(word for word in query.split(' ') if word)

    r = requests.get('https://api.opendota.com/api/explorer', params=dict(sql=query))
    r.raise_for_status()
    result = r.json()
    rows = result['rows']
    return rows


class TimeSeries(pd.Series):
    def __init__(self, *args: Tuple, **kwargs: Dict):
        super().__init__(*args, **kwargs)

    def t(self, start_time: int = None, end_time: int = None) -> pd.Series:
        if start_time is not None and end_time is not None:
            series = self[(self.index >= start_time) & (self.index <= end_time)]
        elif start_time is not None and end_time is None:
            series = self[(self.index >= start_time)]
        elif end_time is not None and start_time is None:
            series = self[(self.index <= end_time)]
        else:
            series = self
        return TimeSeries(series)


class TimeTable(pd.DataFrame):
    def __init__(self, *args: Tuple, **kwargs: Dict):
        super().__init__(*args, **kwargs)

    def t(self, start_time: int = None, end_time: int = None) -> pd.DataFrame:
        if start_time is not None and end_time is not None:
            df = self[(self['time'] >= start_time) & (self['time'] <= end_time)]
        elif start_time is not None and end_time is None:
            df = self[(self['time'] >= start_time)]
        elif end_time is not None and start_time is None:
            df = self[(self['time'] <= end_time)]
        else:
            df = self
        return TimeTable(df)


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


def flatten(list_of_lists: List) -> List:
    return [item for sublist in list_of_lists for item in sublist]
