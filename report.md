# Report 1: Data, Service and ML Brief

**Group:** Grace Diagoné
**Repository:** https://github.com/Yass20mi/Big-data-Checkpoint-1

## 1. Stream

- **Domain:** Weather in 8 French cities (Paris, Lyon, Marseille, Toulouse, Lille, Bordeaux, Nantes, Strasbourg).
- **Source:** Open-Meteo Forecast API (current weather).
- **Endpoint:** `https://api.open-meteo.com/v1/forecast?latitude=...&longitude=...&current=temperature_2m,relative_humidity_2m,precipitation,pressure_msl,wind_speed_10m,cloud_cover&timezone=GMT`
  All 8 cities are requested in one call (comma-separated latitudes and longitudes).
- **Protocol:** REST over HTTPS, JSON response. Our Python producer polls the API every 15 minutes.
- **Sample payload** (real test, Paris, 2026-11-05 21:30 UTC):

    {
      "latitude": 48.853382,
      "longitude": 2.355208,
      "timezone": "GMT",
      "elevation": 46,
      "current_units": {"time": "iso8601", "interval": "seconds",
                        "temperature_2m": "°C", "wind_speed_10m": "km/h"},
      "current": {"time": "2026-11-05T21:30", "interval": 900,
                  "temperature_2m": 10, "wind_speed_10m": 5.4}
    }

- **Expected throughput:** values are updated every 15 min (`"interval": 900`).
  8 cities x 4 updates per hour = 32 events/hour = about 770 events/day = **about 0.01 events/second**.
  Because the live stream is small, we will add historical hourly data from the same source
  (Open-Meteo Historical Weather API, available since 1940) for the ML part.
- **Licence:** CC BY 4.0 (attribution: "Weather data by Open-Meteo.com"), free for non-commercial use.
- **Rate limits:** 10,000 calls/day, 5,000/hour, 600/minute. Each city counts as one call,
  so we use 8 x 96 = 768 calls/day (less than 8% of the limit).
- **Keys:** no API key needed.

## 2. Problem and service

- **Question:** What will the temperature be in one hour in each city?
  We also monitor bad weather (strong wind, heavy rain, frost) in real time.
- **KPIs on the Grafana dashboard:**
  - Domain: current temperature per city; hourly average / min / max temperature;
    precipitation per hour; wind speed; number of alerts (wind > 50 km/h, rain > 4 mm/h, temperature < 0 °C).
  - Pipeline health: events received per minute, input vs processed rows per second, batch duration.
  - Model quality: predicted vs actual temperature, average error over the last 24 hours.

## 3. Kafka message

- **Topic:** `weather.current`, 6 partitions, replication factor 3, retention 7 days.
- **Key:** `city_id` (e.g. `paris`). Same city -> same partition -> events of a city stay in order.
- **Value (JSON):**

| Field | Type | Example |
|---|---|---|
| event_id | string | paris_2026-11-05T21:30 |
| city_id | string | paris |
| event_time | timestamp (UTC) | 2026-11-05T21:30:00Z |
| ingest_time | timestamp (UTC) | 2026-11-05T21:31:12+00:00 |
| temperature_2m | double (°C) | 10.0 |
| relative_humidity_2m | double (%) | 87 |
| precipitation | double (mm) | 0.0 |
| pressure_msl | double (hPa) | 1021.3 |
| wind_speed_10m | double (km/h) | 5.4 |
| cloud_cover | double (%) | 100 |

- **Event-time field:** `event_time`, taken from `current.time` in the API response. **Time zone: UTC.**
  `ingest_time` is the time our producer received the data (UTC).
- **Duplicates:** `event_id` = city + observation time, so the same observation always has the same id;
  Spark removes duplicates with `dropDuplicates("event_id")`.

## 4. ML task

- **Target:** temperature of the city **1 hour later** (regression, in °C).
- **Features:** current temperature, humidity, pressure, wind speed, cloud cover, precipitation,
  hour of the day, day of the year, temperatures of the last 3 hours, city.
- **Model:** Spark MLlib (GBTRegressor) trained on the HDFS data on YARN, tuned with CrossValidator.
- **Baseline to beat:** persistence: "the temperature in 1 hour = the temperature now" (last value).
- **Evaluation metric:** MAE (mean absolute error, in °C); RMSE as a second metric.

## 5. Status

- GitHub repository created (README, producer, this report).
- Producer `producer.py` running on VM ESILV-MCSCIN5A1826-ST-0024: it collects the 8 cities
  every 15 minutes and stores the raw events in `data/weather.jsonl`.
