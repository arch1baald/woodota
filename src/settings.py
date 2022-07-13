import os
from os.path import join
from dotenv import load_dotenv, find_dotenv
from loguru import logger


env_file_exists = load_dotenv()
logger.info(f'.env file exists: {True if find_dotenv() else False}')


ROOT_DIR = join(os.path.dirname(os.path.abspath(__file__)), '..')
logger.info(f'{ROOT_DIR=}')


REPLAY_DIR = join(ROOT_DIR, 'replays')
if not os.path.exists(REPLAY_DIR):
    logger.info('Replay dir is not found, creating...')
    os.mkdir(REPLAY_DIR)
logger.info(f'{REPLAY_DIR=}')


REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost')
logger.info(f'{REDIS_URL=}')
