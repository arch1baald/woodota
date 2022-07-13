from celery import Celery

from settings import REDIS_URL


app = Celery(
    'async_parser',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['async_parser.tasks'],
    accept=['json']
)


if __name__ == '__main__':
    app.start()
