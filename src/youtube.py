import os
import subprocess
import json
from functools import lru_cache
from pathlib import Path
from typing import Tuple, List, Dict
from datetime import datetime, timedelta
from collections import Counter

import yt_dlp
import cv2
import numpy as np
import transformers
from loguru import logger
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image

from settings import YOUTUBE_DIR, VIDEO_DIR, FRAMES_DIR, TIMESTAMPS_DIR
from search import search_top1
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


def process_frames(video_id: str | int, force: bool = False, frames_limit: int = None):
    timestamps_path = TIMESTAMPS_DIR / f'{video_id}.jsonlines'
    if timestamps_path.exists() and not force:
        logger.info(f'Timestamps log already exitst: {timestamps_path}')
        return

    files = sorted(os.listdir(FRAMES_DIR))
    i = 0
    for file in files:
        if not file.startswith(video_id) or (file == '.DS_Store'):
            continue
        i += 1
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

        if frames_limit is not None and (i >= frames_limit):
            logger.info(f'Reached frames limit: {frames_limit}')
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


def generate_team_pairs(matches: List[Dict]) -> Dict:
    pairs = dict()
    for m in matches:
        match_id = m['match_id']
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
    return pairs


def search_team_pairs(teams_pair: str, matches: List[Dict]) -> int:
    pairs = generate_team_pairs(matches)
    candidate = search_top1(teams_pair, list(pairs))
    match_id = pairs[candidate]
    return match_id


def generate_team_tournaments(matches: List[Dict]) -> Dict:
    team_tournaments = dict()
    pairs = generate_team_pairs(matches)
    for m in matches:
        match_id = m['match_id']
        league = m['league']
        for pair, pair_match_id in pairs.items():
            if match_id == pair_match_id:
                team_tournament = f'{pair} | {league}'
                team_tournaments[team_tournament] = match_id
    return team_tournaments


def search_team_tournament_pairs(teams_pair: str, tournament: str, matches: List[Dict]) -> int:
    team_tournament = f'{teams_pair} | {tournament}'
    team_tournaments = generate_team_tournaments(matches)
    candidate = search_top1(team_tournament, list(team_tournaments))
    match_id = team_tournaments[candidate]
    return match_id


def search_teams_after_tournament(teams_pair: str, tournament: str, matches: List[Dict]) -> int:
    leagues = [m['league'] for m in matches]
    tournament_candidate = search_top1(tournament, leagues)
    tournament_matches = [m for m in matches if m['league'] == tournament_candidate]
    tournament_pairs = generate_team_pairs(tournament_matches)
    tournament_pairs_list = list(tournament_pairs.keys())
    candidate = search_top1(teams_pair, tournament_pairs_list)
    match_id = tournament_pairs[candidate]
    return match_id


def search_match(metadata: Dict) -> Tuple[Dict, int]:
    # TODO: test on another channels
    title = metadata['fulltitle']
    upload_date = metadata['upload_date']
    upload_date = datetime.strptime(upload_date, '%Y%m%d')
    matches = get_nearest_matches(upload_date)

    channel_id = metadata['channel_id']
    if channel_id == 'UCUqLL4VcEy4mXcQL0O_H_bg':
        teams_pair, _, tournament = [t.strip() for t in title.split('-')]
        tournament = tournament.replace('Dota 2 Highlights', '')
        title = f'{teams_pair} | {tournament}'
    else:
        raise ValueError(f'Unknown channel: {channel_id}')

    match_ids = [
        search_team_pairs(teams_pair, matches),
        search_team_tournament_pairs(teams_pair, tournament, matches),
        search_teams_after_tournament(teams_pair, tournament, matches),
    ]
    logger.debug(Counter(match_ids))
    selected_match_id, confidence = Counter(match_ids).most_common(1)[0]

    match = [m for m in matches if m['match_id'] == selected_match_id][0]
    match['video_url'] = metadata['webpage_url']
    match['chennel_id'] = channel_id
    match['title'] = title
    match['confidence'] = confidence
    logger.debug(f'Video Title: {title}')
    logger.debug(f'Match Found: {match}')

    with open(YOUTUBE_DIR / 'matches.jsonlines', 'a') as fout:
        json.dump(match, fout)
        fout.write('\n')
    return match, confidence


def analyze_video(
    url: str,
    min_confidence: int = 3,
    keep_video: bool = False,
    keep_frames: bool = False,
    force_process: bool = False,
    frames_limit: int = None,
):
    """Download video from youtube, extract frames, analyze image, parse time, find match_id by title"""
    logger.debug(f'{url=}, {min_confidence=}, {keep_video=}, {keep_frames=}, {force_process=}, {frames_limit=}')

    video_id, metadata = get_video_metadata(url, save=True)
    match, confidence = search_match(metadata)
    if confidence < min_confidence:
        return

    download_video(url)
    video_path = VIDEO_DIR / f'{video_id}.mp4'
    video_info_path = VIDEO_DIR / f'{video_id}.json'

    sample_frames(video_id)

    if not keep_video:
        logger.info(f'Video removed: {video_id}')
        os.remove(video_path)
        os.remove(video_info_path)

    process_frames(video_id, force_process, frames_limit)

    if not keep_frames:
        logger.info(f'Frames removed: {video_id}')
        for file in os.listdir(FRAMES_DIR):
            if file.startswith(video_id):
                os.remove(FRAMES_DIR / file)
