import os
import sys
import time

import requests
from loguru import logger

sys.path.append('src')
sys.path.append(os.path.join('..', 'src'))
from settings import REPLAY_DIR


def main():
    with open(os.path.join(REPLAY_DIR, 'urls.txt'), 'r') as fin:
        for url in fin:
            url = url.strip()

            try:
                r = requests.get('http://localhost:5000/parse', params=dict(url=url))
                r.raise_for_status()
            except Exception as e:
                logger.info(e)
                continue
            
            logger.info(r.json())
            time.sleep(0.05)


if __name__ == '__main__':
    main()
