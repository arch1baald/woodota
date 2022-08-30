# Run Redis
REDIS_CONTAINER=dota-redis
# if  [[ $(docker ps -f "name=$REDIS_CONTAINER" --format '{{.Names}}') == $REDIS_CONTAINER ]]
if [ "$(docker container inspect -f '{{.State.Running}}' $REDIS_CONTAINER)" == "true" ]
then
    echo 'Container ID:' $(docker ps -f name=$REDIS_CONTAINER --format '{{.ID}}')
else
    docker run --name $REDIS_CONTAINER -p 6379:6379 -d redis
fi

# Run Workers
PYTHONPATH=src celery -A async_parser worker -l INFO