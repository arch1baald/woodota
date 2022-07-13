import argparse
import os
import sys
import time

import requests
from loguru import logger

sys.path.append('src')
sys.path.append(os.path.join('..', 'src'))
from settings import REPLAY_DIR


INTERNATIONAL_2021_ID = 13256


def get_matches_by_tournament_id(tournament_id):
    r = requests.get(f'https://api.opendota.com/api/leagues/{tournament_id}/matches')
    matches = r.json()
    logger.info(f'Replays available: {len(matches)}')
    return matches


def get_replays_metadata(tournament_id, limit=None):
    matches = get_matches_by_tournament_id(tournament_id)
    replays = []
    for i, m in enumerate(matches):
        if limit is not None and i >= limit:
            break
        
        match_id = m['match_id']
        logger.info(f'Retrieving replay for the match: {match_id}...')

        try:
            r = requests.get('https://api.opendota.com/api/replays/', params=dict(match_id=match_id))
            r.raise_for_status()
        except Exception as e:
            logger.debug(e)
            break

        replays.append(r.json())
        time.sleep(0.05)
    return replays


def get_replay_urls(tournament_id, limit=None):
    replays = get_replays_metadata(tournament_id, limit)
    urls = []
    for replay in replays:
        cluster = replay[0]['cluster']
        match_id = replay[0]['match_id']
        replay_salt = replay[0]['replay_salt']
        url = f'http://replay{cluster}.valve.net/570/{match_id}_{replay_salt}.dem.bz2'

        r = requests.head(url)
        logger.info(f'Status: {r.status_code}, URL: {url}')
        if r.status_code == 200:
            urls.append(url)
    logger.info(f'The total number of valid URLs: {len(urls)}')
    return urls


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--limit', dest='limit', type=int, 
        default=None, help='Requests Limit to /api/replay'
    )
    parser.add_argument(
        '--tournament', dest='tournament_id', type=int,
        default=INTERNATIONAL_2021_ID, help='Tournament ID'
    )
    args = parser.parse_args()

    logger.info(f'{args.tournament_id}, {args.limit}')
    urls = get_replay_urls(args.tournament_id, args.limit)
    with open(os.path.join(REPLAY_DIR, 'urls.txt'), 'w') as fout:
        for url in urls:
            fout.write(f'{url}\n')
    return urls


if __name__ == '__main__':
    main()
