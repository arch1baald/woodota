import logging
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
