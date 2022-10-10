REDIS_CONTAINER=dota_redis
docker run --name $REDIS_CONTAINER -p 6379:6379 -d redis