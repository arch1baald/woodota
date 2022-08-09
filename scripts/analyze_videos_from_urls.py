import argparse
import sys
import traceback

from loguru import logger

sys.path.append('src')
sys.path.append('../src')
from settings import YOUTUBE_DIR  # noqa
from youtube import analyze_video  # noqa


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--videos-limit', dest='videos_limit', type=int,
        default=None, help='Requests Limit to /api/replay'
    )
    parser.add_argument(
        '--min-confidence', dest='min_confidence', type=bool,
        default=3, help='Minimal confidence for title matching algorithm'
    )
    parser.add_argument(
        '--keep-video', dest='keep_video', type=bool,
        default=False, help='Keep video file after processing'
    )
    parser.add_argument(
        '--keep-frames', dest='keep_frames', type=bool,
        default=False, help='Keep frames after processing'
    )
    parser.add_argument(
        '--force', dest='force_process', type=bool,
        default=False, help='Reanalyze if video already processed'
    )
    parser.add_argument(
        '--frames-limit', dest='frames_limit', type=int,
        default=None, help='Reanalyze if video already processed'
    )
    args = parser.parse_args()

    with open(YOUTUBE_DIR / 'urls.txt', 'r') as fin:
        for i, url in enumerate(fin):
            if args.videos_limit is not None and i >= args.videos_limit:
                break

            url = url.strip()
            try:
                analyze_video(
                    url,
                    args.min_confidence,
                    args.keep_video,
                    args.keep_frames,
                    args.force_process,
                    args.frames_limit,
                )
            except Exception:
                logger.error(traceback.format_exc())
                continue


if __name__ == '__main__':
    main()
