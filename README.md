# dota-highlights
Extracts highlights from professional Dota 2 matches.

Create a virtual environment<br>
`python3 -m virtualenv env`<br>
`source env/bin/activate`

Load dependencies<br>
`pip install -r requirements.txt`

Retrieve replay URLs by Tournament ID (Could be found at the end of Dotabuff [links](https://www.dotabuff.com/esports/leagues/13256-the-international-2021)). The result will be saved to `replays/urls.txt`<br>
`python scripts/retrieve_match_urls.py --tournament 13256 --limit 15`

Run Clarity Parser Server<br>
`sh scripts/run_clarity.sh`

Run Redis and Celery Workers<br>
`sh scripts/run_workers.sh`

Run Flask API<br>
`sh scripts/run_server.sh`

Parse match by URL<br>
`curl -X GET 'http://localhost:5000/parse?url=http://replay191.valve.net/570/6216665747_89886887.dem.bz2'`

Parse first match from `urls.txt`<br>
`curl -X GET -G 'http://localhost:5000/parse' -d url=$(head -n 1 replays/urls.txt)`

Parse all matches from `urls.txt`<br>
`python scripts/parse_from_urls.py`
