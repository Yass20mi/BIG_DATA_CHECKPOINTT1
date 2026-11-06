import json, time, os, urllib.request
from datetime import datetime, timezone

# The 9 weather variables we chose
VARS = ("temperature_2m,relative_humidity_2m,pressure_msl,wind_speed_10m,"
        "wind_speed_100m,wind_direction_10m,rain,snowfall,cloud_cover")

# Météo-France API, Paris, current weather, time in UTC
URL = ("https://api.open-meteo.com/v1/meteofrance?latitude=48.8534&longitude=2.3488"
       "&current=" + VARS + "&timezone=GMT")

os.makedirs("data", exist_ok=True)

while True:                                   # repeat forever
    try:
        # 1. ask the API and read the answer
        c = json.load(urllib.request.urlopen(URL, timeout=30))["current"]

        # 2. build the message (same fields as in our report, part 3)
        msg = {"event_id": "paris_" + c["time"],
               "schema_version": 1,
               "location": "paris",
               "time": c["time"] + ":00Z",
               "ingest_time": datetime.now(timezone.utc).isoformat()}
        msg.update({k: c.get(k) for k in VARS.split(",")})

        # 3. save it: one line per event
        with open("data/weather_paris.jsonl", "a") as f:
            f.write(json.dumps(msg) + "\n")
        print(msg["ingest_time"], "ok", flush=True)

    except Exception as e:
        print("error", e, flush=True)

    time.sleep(900)                           # 4. wait 15 minutes
