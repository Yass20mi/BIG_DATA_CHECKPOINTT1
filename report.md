# Report 1: Data, Service and ML Brief

**Group:** Grace Diagoné
**Repository:** https://github.com/Yass20mi/Big-data-Checkpoint-1
**Date:** November 5, 2026

---

## 1. Our data stream

**What data?** We use live weather data for 8 French cities: Paris, Lyon, Marseille, Toulouse, Lille, Bordeaux, Nantes and Strasbourg.

**Where does it come from?** From Open-Meteo, a free weather website with an API. We do not need an account or an API key.

**How do we get it?** We send a normal web request (REST, HTTPS). The answer is in JSON.
We ask for the 8 cities in one single request: we give the 8 latitudes and the 8 longitudes, separated by commas.


https://api.open-meteo.com/v1/forecast
  ?latitude=48.85,45.76,43.3,43.6,50.63,44.84,47.22,48.57
  &longitude=2.35,4.84,5.37,1.44,3.06,-0.58,-1.55,7.75
  &current=temperature_2m,relative_humidity_2m,precipitation,pressure_msl,wind_speed_10m,cloud_cover
  &timezone=GMT


**What do we measure?** Temperature (°C), humidity (%), rain (mm), air pressure (hPa), wind speed (km/h) and cloud cover (%).

<img width="672" height="319" alt="image" src="https://github.com/user-attachments/assets/e7d6e3b2-961c-43e6-a6b7-755796d19d8d" />


**How many events?** 8 cities, updated 4 times per hour = 32 events per hour, about 770 per day.
That is about **0.01 events per second**. This is small, so for the machine learning part we will also download past weather data from Open-Meteo (they have data since 1940).

**Licence and limits:** the data is under the CC BY 4.0 licence (we must write "Weather data by Open-Meteo.com"). The free version allows 10,000 requests per day. We use about 770 per day, so we are far below the limit.

## 2. Our question and our dashboard

**The question:** *What will the temperature be in one hour in each city?*
We also want to see bad weather quickly: strong wind, heavy rain or frost.

**What the dashboard (Grafana) will show:**
- The weather: the temperature now in each city, the average, minimum and maximum per hour, the rain, the wind, and the number of alerts (wind over 50 km/h, rain over 4 mm per hour, temperature under 0 °C).
- The health of the pipeline: how many events arrive per minute, how fast Spark processes them, and the time since the last event of each city.
- The quality of the model: the predicted temperature next to the real temperature, and the average error.

## 3. Our Kafka message

We will send one message per city, every 15 minutes, to the Kafka topic `weather.current`.
The topic will have 6 partitions and a replication factor of 3 (one copy on each of our 3 Kafka machines). Messages are kept for 7 days.

**Key:** `city_id` (for example `paris`). All the messages of one city go to the same partition, so they stay in the right order.

**Value:** a JSON message with these fields:

| Field | Type | Meaning |
|---|---|---|
| event_id | text | unique id = city + time of the measure |
| city_id | text | name of the city |
| event_time | date and time (UTC) | when the weather was measured |
| ingest_time | date and time (UTC) | when our program received it |
| temperature_2m | number | temperature in °C |
| relative_humidity_2m | number | humidity in % |
| precipitation | number | rain in mm |
| pressure_msl | number | air pressure in hPa |
| wind_speed_10m | number | wind speed in km/h |
| cloud_cover | number | clouds in % |

**Time:** the event time is `event_time`. It comes from the API and it is in **UTC**.

**Why an event_id?** If our program restarts, it can send the same measure twice. The two copies have the same `event_id`, so Spark can delete the duplicate.

**A real message made by our program** (first line of our data file on the VM):
```json
{"event_id": "paris_2026-11-05T22:15", "city_id": "paris",
 "event_time": "2026-11-05T22:15:00Z", "ingest_time": "2026-11-05T22:21:50.254915+00:00",
 "temperature_2m": 9.8, "relative_humidity_2m": 72, "precipitation": 0.0,
 "pressure_msl": 1023.1, "wind_speed_10m": 4.2, "cloud_cover": 100}
```
The weather was measured at 22:15 and our program got it at 22:21. This is why we keep both times.

## 4. Our machine learning task

- **What we predict (target):** the temperature in each city **one hour later**.
- **What we use to predict (features):** the weather now (temperature, humidity, pressure, wind, clouds, rain), the hour of the day, the day of the year, the temperature of the last 3 hours, and the city.
- **Data for training:** the data we collect + past data from Open-Meteo, saved in HDFS. We train on the past and test on the most recent weeks.
- **Model:** a Spark MLlib model (Gradient-Boosted Trees), trained on our cluster.
- **Baseline (the simple guess to beat):** "the temperature in one hour will be the same as now".
- **How we measure the error:** MAE, the average error in degrees (°C). For example, MAE = 0.5 means we are wrong by 0.5 °C on average.

## 5. Data collection: started

- Our program `producer.py` is written in Python. It runs on our virtual machine **ESILV-MCSCIN5A1826-ST-0024** (name `master`).
- **It started on November 5, 2026 at 22:21 UTC.** The first line of its log says: `2026-11-05T22:21:50.254915+00:00 ok 8 villes`.
- Every 15 minutes, it asks Open-Meteo for the weather of the 8 cities and adds 8 new lines to the file `data/weather.jsonl`.
- For now, the data is saved in a file because Kafka is not installed yet. In checkpoint 2, we will install Kafka and HDFS, and the program will send its messages to Kafka. We will also send the lines already collected.

 Grace Yasmibe GitHub repository, producer program, data collection on the VM, this report.

