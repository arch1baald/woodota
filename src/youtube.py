import os
import subprocess
import json
from functools import lru_cache
from pathlib import Path
from typing import Tuple, List, Dict
from datetime import datetime, timedelta

import yt_dlp
import cv2
import numpy as np
import transformers
from loguru import logger
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image

from settings import VIDEO_DIR, FRAMES_DIR, TIMESTAMPS_DIR
from search import search, search_top1
from utils import DisableLogger, EmptyDebugLogger, query_opendota


@lru_cache
def get_video_metadata(url: str, save: bool = False) -> Tuple[str | int, dict]:
    options = dict(
        logger=EmptyDebugLogger,
    )
    with yt_dlp.YoutubeDL(options) as ydl:
        metadata = ydl.extract_info(url, download=False)
    video_id = metadata.get('id')

    if save:
        metadata_file = f'{video_id}.json'
        video_metadata_path = VIDEO_DIR / metadata_file
        with open(video_metadata_path, 'w') as fout:
            json.dump(metadata, fout, indent=4)
    return video_id, metadata


def download_video(url: str, fetch_metadata: bool = True) -> str | int:
    options = dict(
        format='mp4',
        outtmpl=f'{VIDEO_DIR}/%(id)s.%(ext)s',
        logger=EmptyDebugLogger,
    )
    video_id, _ = get_video_metadata(url, save=fetch_metadata)
    video_file = f'{video_id}.mp4'
    video_path = VIDEO_DIR / video_file
    if video_path.exists():
        logger.info(f'Video already exists: {video_path}')
        return video_id

    logger.info(f'Downloading: {url}')
    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download(url)
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
    model_version = 'microsoft/trocr-base-printed'
    logger.info(f'Loading model from: {model_version}')
    transformers.logging.set_verbosity_error()
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


def get_nearest_matches(date: datetime) -> List[Dict]:
    end_time = date + timedelta(days=1)
    start_time = date - timedelta(days=2)
    query = '''
    SELECT
        match_id,
        start_time,
        matches.leagueid,
        leagues.name as league,
        radiant_team_id,
        radiant_team.name as radiant_name,
        radiant_team.tag as radiant_tag,
        dire_team_id,
        dire_team.name as dire_name,
        dire_team.tag as dire_tag
    FROM
        matches
        join teams as dire_team on matches.dire_team_id = dire_team.team_id
        join teams as radiant_team on matches.radiant_team_id = radiant_team.team_id
        join leagues on matches.leagueid = leagues.leagueid
    WHERE
        start_time >= extract(epoch from timestamp '{start_time}')
        and start_time <= extract(epoch from timestamp '{end_time}')
    ORDER BY
        start_time desc
    LIMIT
        100
    '''
    matches = query_opendota(
        query,
        start_time=datetime.strftime(start_time, '%m-%d-%Y'),
        end_time=datetime.strftime(end_time, '%m-%d-%Y')
    )
    return matches


def generate_candidates(matches: Dict) -> Tuple[Dict, Dict]:
    titles = dict()
    pairs = dict()
    for m in matches:
        match_id = m['match_id']
        league = m['league']
        radiant_tag = m['radiant_tag']
        dire_tag = m['dire_tag']
        radiant_name = m['radiant_name']
        dire_name = m['dire_name']

        name_pair_1 = f'{radiant_name} vs {dire_name}'
        name_pair_2 = f'{dire_name} vs {radiant_name}'
        tag_pair_1 = f'{radiant_tag} vs {dire_tag}'
        tag_pair_2 = f'{dire_tag} vs {radiant_tag}'
        for pair in (name_pair_1, name_pair_2, tag_pair_1, tag_pair_2):
            pairs[pair] = match_id

        title_from_names_1 = f'{name_pair_1} | {league}'
        title_from_names_2 = f'{name_pair_2} | {league}'
        title_from_tags_1 = f'{tag_pair_1} | {league}'
        title_from_tags_2 = f'{tag_pair_2} | {league}'
        for title in (title_from_names_1, title_from_names_2, title_from_tags_1, title_from_tags_2):
            titles[title] = match_id
    return pairs, titles


def search_match(metadata: Dict) -> Tuple[Dict, int]:
    # TODO: add tournament search
    # TODO: add search without Dota 2 Highlights
    # TODO: add search without comment in the middle
    # TODO: test on another channels
    title = metadata['fulltitle']
    upload_date = metadata['upload_date']
    upload_date = datetime.strptime(upload_date, '%Y%m%d')
    matches = get_nearest_matches(upload_date)

    pairs, titles = generate_candidates(matches)
    pairs_list, titles_list = list(pairs.keys()), list(titles)

    candidate_from_pairs = search_top1(title, pairs_list)
    candidate_from_titles = search_top1(title, titles_list)
    match_id_from_pairs = pairs[candidate_from_pairs]
    match_id_from_titles = titles[candidate_from_titles]

    confidence = 0
    confidence += match_id_from_pairs == match_id_from_titles

    match = [m for m in matches if m['match_id'] == match_id_from_titles][0]
    logger.debug(f'Video Title: {title}')
    logger.debug(f'Match Found: {match}, Confidence: {confidence}')
    return match, confidence


def main(keep_video: bool = True, keep_frames: bool = True, force_process: bool = False):
    urls = [
        # 'https://youtu.be/sNj5QAzujAM',
        'https://youtu.be/ukbICbM4RR0',
    ]

    for url in urls:
        video_id, metadata = get_video_metadata(url, save=True)
        download_video(url)
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

        match, confidene = search_match(metadata)


if __name__ == '__main__':
    main()
