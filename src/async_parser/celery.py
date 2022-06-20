from celery import Celery


app = Celery(
    'async_parser',
    broker='redis://localhost',
    backend='redis://localhost',
    include=['async_parser.async_parser'],
    accept=['json', 'pickle']
)


if __name__ == '__main__':
    app.start()
