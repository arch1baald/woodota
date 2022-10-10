import sys
import pytest
import json
from typing import Dict

import numpy as np

sys.path.append('src')
sys.path.append('../src')
from settings import FIXTURES_DIR  # noqa E402


@pytest.fixture
def video_url() -> str:
    return 'https://youtu.be/wUPhtY4sNP0'


@pytest.fixture
def video_id() -> str:
    return 'wUPhtY4sNP0'


@pytest.fixture
def test_frame_file() -> str:
    return 'wUPhtY4sNP0__001.bmp'


@pytest.fixture
def test_frame(test_frame_file: str) -> np.ndarray:
    import cv2

    path = str(FIXTURES_DIR / test_frame_file)
    image = cv2.imread(path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return image


@pytest.fixture
def test_highlights_response() -> Dict:
    path = FIXTURES_DIR / '6676393091_highlights.json'
    with open(path, 'r') as fin:
        response = json.load(fin)
    return response
