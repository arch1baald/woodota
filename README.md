# WoDota
Extract highlights from professional Dota 2 matches.

A few minutes of nostalgia.
<iframe width="1496" height="583" src="https://www.youtube.com/embed/P4L2mo8fH8I" title="DotA - WoDotA Top10 Weekly Vol.1" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>


## TODO
- [ ] Important: Fix clarity-parser for Linux (MacOS M1 works well)
- [ ] Write the final notebook
- [ ] Refactor youtube.py
- [ ] Add youtube to docker-compose or move to another repo
- [ ] Write tests

## Quick Start
### Environment
Create a `.env` file and select your os platform. There are two possible choices right now:
- linux
- macos
```
touch .env
echo OS_PLATFORM=macos >> .env
```

### Docker
Run Docker containers.
```
docker-compose --env-file .env up
```

### Match ID
Each match in Dota 2 has a Match ID. You can find it at the end of Dotabuff links or in the game client.

For example: 6216665747 with Dotabuff: https://dotabuff.com/matches/6216665747.

Notice: Replays of non-professional matches are stored for 2 weeks.

### Retrieve URL
To retrieve an URL of the match replay
```
curl -X GET http://localhost:8000/retrieve/6676393091
```
Or just follow the link: http://localhost:8000/retrieve/6676393091.

### Parse Replay
```
curl -X GET 'http://localhost:8000/parse?url=http://replay161.valve.net/570/6676393091_316408452.dem.bz2'
```
The process takes about a minute, depends on the internet connection and compute resources.

### Extract Highlights
To extract highlights from the match replay.
```
curl -X GET http://localhost:8000/getHighlights/6676393091
```
Or just follow the link: http://localhost:8000/getHighlights/6676393091.

## YouTube
### Install dependencies
```
python3 -m virtualenv env
source env/bin/activate
pip install -r requirements.txt
```

### Run Jupyter
```
jupyter lab
```

Open [`notebooks/piterpy.ipynb`](https://github.com/arch1baald/dota-highlights/blob/piterpy/notebooks/piterpy.ipynb) and follow the instructions.

## OLD non-structured docs

Parser repo: https://github.com/arch1baald/clarity-parser

Rebuild API
```
docker-compose up -d --build --no-deps api
```

### Build and Run Clarity Parser Server
```
sh scripts/run_clarity.sh
```

### Run Redis and Celery Workers
```
sh scripts/run_workers.sh
```

### Run Flask API
Open a new terminal window<br>
```
source env/bin/activate
sh scripts/run_server.sh
```

## Retrieve URLs
Retrieve replay URLs by Tournament ID (Could be found at the end of Dotabuff [links](https://www.dotabuff.com/esports/leagues/13256-the-international-2021)). The result will be saved to `replays/urls.txt`<br>
```
python scripts/retrieve_match_urls.py --tournament 13256 --limit 15
```

## Parse Matches
Parse match by URL<br>
```
curl -X GET 'http://localhost:8000/parse?url=http://replay191.valve.net/570/6216665747_89886887.dem.bz2'
```

Parse first match from `urls.txt`<br>
```
curl -X GET -G 'http://localhost:8000/parse' -d url=$(head -n 1 replays/urls.txt)
```

Parse all matches from `urls.txt`<br>
```
python scripts/parse_from_urls.py
```
