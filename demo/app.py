"""Local browser demo. No web framework or paid API is required."""

import argparse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
from threading import Lock
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from travel_constraints.planner import apply_constraints
from travel_constraints.weather import fetch_london_forecast, rain_in_window
from travel_constraints.extraction import LocalExtractor
from travel_constraints.evidence_guard import normalize
from travel_constraints.contract import validate_output
from travel_constraints.coverage import complete_extraction

EXAMPLES = json.loads((ROOT / "demo/saved_examples.json").read_text())
PLACES = json.loads((ROOT / "data/reference/london_places.json").read_text())
FORECAST_PATH = ROOT / "data/reference/london_forecast.json"
FORECAST = json.loads(FORECAST_PATH.read_text())
LOCK = Lock()
EXTRACTOR = None


def extractor_description():
    # Saved examples must remain usable without model files or MLX installed.
    config = ROOT / "outputs/runtime/extractor_config.json"
    if config.is_file():
        settings = json.loads(config.read_text())
        label = settings["primary"].get("label", "Local Transformer")
        return (label + (" with schema-validated fallback" if settings.get("fallback") else "")
                + (" + request consistency checks" if settings.get("evidence_checks") else ""))
    return "Qwen2.5-0.5B-Instruct + LoRA"


def get_extractor():
    global EXTRACTOR
    if EXTRACTOR is None:
        config = ROOT / "outputs/runtime/extractor_config.json"
        if config.is_file():
            EXTRACTOR = LocalExtractor.from_config(config)
        else:
            manifest = json.loads((ROOT / "outputs/runtime/small_model.json").read_text())
            EXTRACTOR = LocalExtractor({"model": manifest["path"],
                                       "adapter": str(ROOT / "artifacts/qwen05_lora"),
                                       "label": "Qwen2.5-0.5B-Instruct + LoRA"})
    return EXTRACTOR


def extract(model_input):
    with LOCK:
        extractor = get_extractor()
        result = extractor.extract(model_input)
        config = ROOT / "outputs/runtime/extractor_config.json"
        settings = json.loads(config.read_text()) if config.is_file() else {}
        enabled = settings.get("evidence_checks", False)
        if not enabled:
            return result
        retries = max(0, min(2, int(settings.get("coverage_retries", 0))))
        if retries:
            result = complete_extraction(model_input, result, extractor.extract, max_retries=retries)
            result['evidence_checks'] = True
            result['coverage_checked'] = True
            return result
        parsed, audit = normalize(model_input, result["parsed_output"])
        errors = validate_output(parsed) if parsed is not None else result["validation_errors"]
        return result | {"model_parsed_output": result["parsed_output"],
                         "parsed_output": None if errors else parsed,
                         "validation_errors": errors, "evidence_checks": True,
                         "normalization_audit": audit}


class Handler(BaseHTTPRequestHandler):
    def respond(self, value, status=200):
        data = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/api/context":
            return self.respond({"examples": EXAMPLES, "forecast": FORECAST, "places": PLACES,
                                 "city": "London", "model": extractor_description()})
        file = ROOT / "demo/static" / ("index.html" if path == "/" else path.lstrip("/"))
        if not file.resolve().is_relative_to((ROOT / "demo/static").resolve()) or not file.is_file():
            return self.respond({"error": "Not found"}, 404)
        mime = {".html": "text/html", ".css": "text/css", ".js": "application/javascript"}.get(file.suffix, "application/octet-stream")
        data = file.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        global FORECAST
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 32768:
                return self.respond({"error": "Request too large or empty"}, 400)
            body = json.loads(self.rfile.read(length))
            if self.path == "/api/weather":
                FORECAST = fetch_london_forecast()
                return self.respond({"forecast": FORECAST})
            if self.path != "/api/extract":
                return self.respond({"error": "Not found"}, 404)
            model_input = body["input"]
            if model_input.get("city") != "London" or len(model_input.get("change_request", "")) > 6000:
                return self.respond({"error": "Use a London reference plan and a request under 6,000 characters."}, 400)
            if body.get("source") == "saved":
                example = next(e for e in EXAMPLES if e["id"] == body["example_id"])
                if model_input != example["input"]:
                    return self.respond({"error": "Saved runs require their original request and reference plan. Select Live model for edited text."}, 400)
                parsed, raw, errors = example["prediction"], example["raw_output"], []
                provenance = {"model_used": "saved", "fallback_used": False}
            else:
                result = extract(model_input)
                parsed, raw, errors = result["parsed_output"], result["raw_output"], result["validation_errors"]
                provenance = {k: result[k] for k in ("model_used", "fallback_used", "attempts")}
                provenance.update({k: result[k] for k in (
                    "model_parsed_output", "evidence_checks", "normalization_audit",
                    "coverage_checked", "coverage_attempts", "coverage_unresolved") if k in result})
            if parsed is None:
                return self.respond({"valid": False, "raw": raw, "errors": errors, "extraction": provenance})
            date = body["date"]
            datetime.fromisoformat(date)
            assessment = rain_in_window(FORECAST, date + "T14:00", date + "T15:00")
            mode = body.get("weather_mode", "forecast")
            rain = True if mode == "rain" else False if mode == "dry" else assessment["rain"]
            plan = apply_constraints(model_input["reference_itinerary"], parsed, rain, PLACES)
            remaining = provenance.get("coverage_unresolved", [])
            if remaining:
                labels = {"hotel_return": "hotel return time", "walking_duration": "walking duration",
                          "walking_amount": "walking preference", "place_visit": "requested visit",
                          "lunch": "lunch location", "*": "weather conditions"}
                names = ", ".join(labels.get(target, target) for _, target in remaining)
                plan["notes"].insert(0, "Some requested conditions were not extracted: " + names + ". Review these before using the plan.")
            self.respond({"valid": True, "constraints": parsed["constraints"], "plan": plan,
                          "weather": assessment | {"rain": rain, "mode": mode}, "raw": raw,
                          "source": body.get("source", "live"), "extraction": provenance})
        except Exception as error:
            self.respond({"error": str(error)}, 400)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    print(f"Open http://127.0.0.1:{args.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
