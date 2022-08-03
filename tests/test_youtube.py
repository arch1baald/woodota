import os

import cv2
import numpy as np

from settings import FRAMES_DIR
from youtube import sample_frames


def test_youtube_download(video_url: str):
    # download_ranges
    pass


def test_sample_frames(video_id: str, test_frame_file: str, test_frame: np.ndarray):
    sample_frames(video_id, force=True)
    files = sorted(os.listdir(FRAMES_DIR))
    for file in files:
        if not file.startswith(video_id) or (file == '.DS_Store'):
            continue

        if file == test_frame_file:
            path = str(FRAMES_DIR / file)
            image = cv2.imread(path)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            assert np.all(image == test_frame)
            break
