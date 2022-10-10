import os
import time
from pathlib import Path
from typing import Dict

# import numpy as np
import requests
from loguru import logger

from settings import (
    # FRAMES_DIR,
    REPLAY_DIR,
)
# from youtube import sample_frames


def test_pytest():
    assert True


def test_api(test_highlights_response: Dict):
    # FIXME: Use celery status job_id instead of timeouts

    host_port = 'http://localhost:8000'
    match_id = 6676393091
    jsonlines = f'{match_id}.jsonlines'
    demfile = f'{match_id}.dem'
    path_jsonlines = Path(REPLAY_DIR) / jsonlines
    path_demfile = Path(REPLAY_DIR) / demfile

    if path_jsonlines.exists():
        os.remove(path_jsonlines)

    logger.info('Test Retriever')
    r = requests.get(f'{host_port}/retrieve/{match_id}')
    content = r.json()
    url = content['url']

    logger.info('Test Parser')
    r = requests.get(f'{host_port}/parse', params=dict(url=url))

    time.sleep(20)
    for _ in range(7):
        if path_demfile.exists():
            time.sleep(10)

    logger.info('Test Highlights')
    r = requests.get(f'{host_port}/getHighlights/{match_id}')
    response = r.json()
    assert response == test_highlights_response


def test_youtube_download(video_url: str):
    # download_ranges
    pass


# def test_sample_frames(video_id: str, test_frame_file: str, test_frame: np.ndarray):
#     import cv2

#     sample_frames(video_id, force=True)
#     files = sorted(os.listdir(FRAMES_DIR))
#     for file in files:
#         if not file.startswith(video_id) or (file == '.DS_Store'):
#             continue

#         if file == test_frame_file:
#             path = str(FRAMES_DIR / file)
#             image = cv2.imread(path)
#             image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
#             assert np.all(image == test_frame)
#             break
