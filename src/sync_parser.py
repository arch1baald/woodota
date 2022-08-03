import os
import time
import requests
import subprocess
from bz2 import decompress

from loguru import logger

from settings import REPLAY_DIR


def download(url: str) -> bytes:
    r = requests.get(url)
    r.raise_for_status()
    compressed_dem = r.content
    dem = decompress(compressed_dem)
    return dem


def download_save(url: str) -> str:
    right = url.split('/')[-1]
    match_salt = right.replace('dem.bz2', '')
    file_name = match_salt.split('_')[0]
    file_name += '.dem'

    dem = download(url)
    path = os.path.join(REPLAY_DIR, file_name)
    with open(path, 'wb') as fout:
        fout.write(dem)
    return path


def download_parse_save(url: str) -> str:
    dem_path = download_save(url)
    jsonlines_path = dem_path.replace('.dem', '.jsonlines')
    cmd = f'curl localhost:5600 --data-binary "@{dem_path}" > {jsonlines_path}'
    subprocess.run(cmd, shell=True)
    return jsonlines_path


def run_sync_parser():
    urls = []
    urls_path = os.path.join(REPLAY_DIR, 'urls.txt')
    with open(urls_path, 'r') as fin:
        for line in fin.readlines():
            urls.append(line.replace('\n', ''))
    logger.info(len(urls))

    for url in urls[:6]:
        started_at = time.time()
        logger.info(url)
        parsed_path = download_parse_save(url)
        elapsed_time = time.time() - started_at
        logger.info(parsed_path)
        logger.info(f'elapsed_time: {round(elapsed_time)} seconds')


if __name__ == '__main__':
    run_sync_parser()
