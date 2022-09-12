# PYTHONPATH=src/ FLASK_APP=server FLASK_RUN_PORT=8008 flask run
FLASK_ENV=${1:-development}
LOGURU_LEVEL=${2:-DEBUG}

if [[ "$FLASK_ENV" != "production" ]]; then
    PYTHONPATH=src \
    FLASK_APP=server \
    FLASK_RUN_HOST=0.0.0.0 \
    FLASK_RUN_PORT=5005 \
    FLASK_ENV=$FLASK_ENV \
    LOGURU_LEVEL=$LOGURU_LEVEL \
    flask run
else
    WORKERS=4
    FLASK_ENV=$FLASK_ENV \
    LOGURU_LEVEL=INFO \
    gunicorn -w $WORKERS --chdir $(pwd)/src "server:app" -b 0.0.0.0:8000
fi
