import json, time, os, urllib.request
from datetime import datetime, timezone

CITIES = {"paris": (48.85, 2.35), "lyon": (45.76, 4.84), "marseille": (43.30, 5.37),
          "toulouse": (43.60, 1.44), "lille": (50.63, 3.06), "bordeaux": (44.84, -0.58),
          "nantes": (47.22, -1.55), "strasbourg": (48.57, 7.75)}
VARS = "temperature_2m,relative_humidity_2m,precipitation,pressure_msl,wind_speed_10m,cloud_cover"
URL = ("https://api.open-meteo.com/v1/forecast?latitude=" + ",".join(str(v[0]) for v in CITIES.values())
       + "&longitude=" + ",".join(str(v[1]) for v in CITIES.values())
       + "&current=" + VARS + "&timezone=GMT")

os.makedirs("data", exist_ok=True)
while True:
    try:
        data = json.load(urllib.request.urlopen(URL, timeout=30))
        now = datetime.now(timezone.utc).isoformat()
        with open("data/weather.jsonl", "a") as f:
            for city, loc in zip(CITIES, data):
                c = loc["current"]
                msg = {"event_id": city + "_" + c["time"], "city_id": city,
                       "event_time": c["time"] + ":00Z", "ingest_time": now}
                msg.update({k: c[k] for k in VARS.split(",")})
                f.write(json.dumps(msg) + "\n")
        print(now, "ok", len(data), "villes")
    except Exception as e:
        print("erreur", e)
    time.sleep(900)  
