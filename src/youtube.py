import os
import subprocess
import json
from functools import lru_cache
from pathlib import Path

import yt_dlp
import cv2
import numpy as np
from loguru import logger
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image

from settings import VIDEO_DIR, FRAMES_DIR, TIMESTAMPS_DIR
from utils import DisableLogger


def youtube_download(url: str) -> str | int:
    options = dict(
        format='mp4',
        outtmpl=f'{VIDEO_DIR}/%(id)s.%(ext)s',
    )
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)
    video_id = info.get('id')
    info_file = f'{video_id}.json'
    video_info_path = VIDEO_DIR / info_file
    video_file = f'{video_id}.mp4'
    video_path = VIDEO_DIR / video_file
    if video_path.exists():
        logger.info(f'Video already exists: {video_path}')
        return video_id

    logger.info(f'Downloading: {url}')
    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download(url)

    with open(video_info_path, 'w') as fout:
        json.dump(info, fout, indent=4)
    return video_id


def sample_frames(video_id: str | int, force: bool = False):
    video_path = VIDEO_DIR / f'{video_id}.mp4'
    output_prefix = FRAMES_DIR / video_id
    if not force:
        for file in os.listdir(FRAMES_DIR):
            if file.startswith(video_id):
                logger.info(f'Frames already exists: {video_id}')
                return

    logger.info(f'Sampling Frames from: {video_id}')
    cmd = f'''ffmpeg \
        -i {str(video_path)} \
        -r 1/1 \
        {str(output_prefix)}__$filename%03d.bmp
    '''
    subprocess.run(cmd, shell=True)


@lru_cache
def load_ocr_model() -> tuple:
    model_version = "microsoft/trocr-base-printed"
    logger.info(f'Loading model from: {model_version}')
    processor = TrOCRProcessor.from_pretrained(model_version)
    model = VisionEncoderDecoderModel.from_pretrained(model_version)
    return processor, model


def crop_frame(frame_path: Path) -> np.ndarray:
    image = cv2.imread(str(frame_path))
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    bbox = (16, 23, 619, 653)
    crop = image[bbox[0]:bbox[1], bbox[2]:bbox[3]]
    crop = cv2.resize(crop, dsize=None, fx=16, fy=16, interpolation=cv2.INTER_CUBIC)
    return crop


def extract_text(image_array: np.ndarray) -> str:
    pil_image = Image.fromarray(image_array)
    processor, model = load_ocr_model()
    pixel_values = processor(pil_image, return_tensors='pt').pixel_values
    generated_ids = model.generate(pixel_values)
    text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return text


def convert_to_timestamp(text: str) -> int:
    sign = -1 if text.startswith('-') else 1
    digits = ''.join([c for c in text if c.isdigit()])
    seconds = digits[-2:]
    seconds = int(seconds)
    minutes = digits[:-2]
    minutes = int(minutes)
    timestamp = sign * (minutes * 60 + seconds)
    return timestamp


def process_frames(video_id: str | int, force: bool = False):
    timestamps_path = TIMESTAMPS_DIR / f'{video_id}.log'
    if timestamps_path.exists() and not force:
        logger.info(f'Timestamps log already exitst: {timestamps_path}')
        return

    files = sorted(os.listdir(FRAMES_DIR))
    for i, file in enumerate(files):
        if not file.startswith(video_id) or (file == '.DS_Store'):
            continue

        frame_id = file.split('__')[-1]
        frame_id = frame_id.replace('.bmp', '')

        path = FRAMES_DIR / file
        crop = crop_frame(path)
        with DisableLogger():
            text = extract_text(crop)
        logger.debug(f'Extracted: {text} | From: {file}')

        try:
            timestamp = convert_to_timestamp(text)
        except Exception as err:
            logger.error(f'{text=}, {err}')
            timestamp = None

        with open(timestamps_path, 'a') as logfile:
            record = dict(
                video_id=video_id,
                frame_id=frame_id,
                text=text,
                timestamp=timestamp,
            )
            logfile.write(json.dumps(record))
            logfile.write('\n')

        if i > 0 and i % 10 == 0:
            break


def main(keep_video: bool = True, keep_frames: bool = True, force_process: bool = False):
    urls = [
        'https://youtu.be/sNj5QAzujAM',
        'https://youtu.be/ukbICbM4RR0',
    ]

    for url in urls:
        video_id = youtube_download(url)
        video_path = VIDEO_DIR / f'{video_id}.mp4'
        video_info_path = VIDEO_DIR / f'{video_id}.json'

        sample_frames(video_id)

        if not keep_video:
            logger.info(f'Video removed: {video_id}')
            os.remove(video_path)
            os.remove(video_info_path)

        process_frames(video_id, force_process)

        if not keep_frames:
            logger.info(f'Frames removed: {video_id}')
            for file in os.listdir(FRAMES_DIR):
                if file.startswith(video_id):
                    os.remove(FRAMES_DIR / file)


if __name__ == '__main__':
    main()
