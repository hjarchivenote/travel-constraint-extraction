"""London forecasts and explicit rain-conditional activation.

Hourly rain/showers totals describe the preceding hour. The demo labels an
overlapping hour rainy at >= 0.1 mm of forecast rain plus showers. This is an
application setting, not a threshold inferred from a user's words.
"""

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
from urllib.parse import urlencode


def fetch_london_forecast():
    query = urlencode({"latitude": 51.5074, "longitude": -0.1278,
                       "hourly": "temperature_2m,precipitation,rain,showers",
                       "models": "ecmwf_ifs025", "forecast_days": 2, "timezone": "Europe/London"})
    url = "https://api.open-meteo.com/v1/forecast?" + query
    # curl uses macOS certificate verification; do not disable TLS checking.
    response = subprocess.run(["curl", "-fsSL", "--connect-timeout", "5", "--max-time", "30", url],
                              capture_output=True, text=True, check=True)
    data = json.loads(response.stdout)
    if "hourly" not in data or "rain" not in data["hourly"] or "showers" not in data["hourly"]:
        raise ValueError("Forecast response lacks the requested rain variables.")
    return {"source_url": url, "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "model": "ecmwf_ifs025", "attribution": "Weather data by Open-Meteo, model ECMWF IFS 0.25°",
            "data": data}


def rain_in_window(snapshot, start, end, threshold_mm=0.1):
    """Assess a local London window; partial hourly buckets are conservative."""
    start, end = datetime.fromisoformat(start), datetime.fromisoformat(end)
    if start >= end:
        raise ValueError("Weather window end must be after its start.")
    if threshold_mm <= 0:
        raise ValueError("Rain threshold must be positive.")
    hourly = snapshot["data"]["hourly"]
    timestamps = hourly["time"]
    rain, showers = hourly.get("rain", []), hourly.get("showers", [])
    if len(rain) != len(timestamps) or len(showers) != len(timestamps):
        raise ValueError("Rain arrays are not aligned with hourly timestamps.")
    coverage, unknown, rainy = 0.0, False, False
    selected = []
    for stamp, rain_mm, shower_mm in zip(timestamps, rain, showers):
        bucket_end = datetime.fromisoformat(stamp)
        bucket_start = bucket_end - timedelta(hours=1)
        overlap = (min(end, bucket_end) - max(start, bucket_start)).total_seconds()
        if overlap <= 0:
            continue
        coverage += overlap
        selected.append(stamp)
        components = [value for value in (rain_mm, shower_mm) if value is not None]
        if sum(components) >= threshold_mm:
            rainy = True
        if len(components) < 2:
            unknown = True
    unknown = unknown or coverage < (end - start).total_seconds()
    return {"rain": True if rainy else None if unknown else False,
            "bucket_ends_local": selected, "threshold_mm_per_hour": threshold_mm,
            "window_policy": "any overlapping hourly bucket; partial hours not prorated",
            "timezone": "Europe/London", "forecast_retrieved_at": snapshot["retrieved_at"]}


def select_applicable_constraints(extracted, rain):
    result = {"active": [], "inactive": [], "pending": []}
    for item in extracted["constraints"]:
        condition = item["condition"]
        if item["needs_clarification"]:
            destination = "pending"
        elif condition is None:
            destination = "active"
        elif rain is None:
            destination = "pending"
        else:
            destination = "active" if condition["occurs"] == rain else "inactive"
        result[destination].append(item)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="outputs/runtime/london_weather.json")
    args = parser.parse_args()
    snapshot = fetch_london_forecast()
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, indent=2))
    hourly = snapshot["data"]["hourly"]
    print(json.dumps({"hours": len(hourly["time"]), "start": hourly["time"][0],
                      "end": hourly["time"][-1], "retrieved_at": snapshot["retrieved_at"]}))


if __name__ == "__main__":
    main()
