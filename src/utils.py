import logging
from typing import Any, List, Dict

import requests
from tenacity import retry, stop_after_attempt, wait_fixed
from loguru import logger


class DisableLogger:
    def __enter__(self):
        logging.disable(logging.CRITICAL)

    def __exit__(self, exception_type: Any, exception_value: Any, traceback: Any):
        logging.disable(logging.NOTSET)


class EmptyDebugLogger:
    def debug(self):
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
