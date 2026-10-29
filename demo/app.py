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

EXAMPLES = json.loads((ROOT / "demo/saved_examples.json").read_text())
PLACES = json.loads((ROOT / "data/reference/london_places.json").read_text())
FORECAST_PATH = ROOT / "data/reference/london_forecast.json"
FORECAST = json.loads(FORECAST_PATH.read_text())
LOCK = Lock()
MODEL = TOKENIZER = None


def extract(model_input):
    global MODEL, TOKENIZER
    from travel_constraints.contract import messages_for, parse_output
    from travel_constraints.download_models import resolve_model_path
    import mlx.core as mx
    from mlx_lm import load, generate
    from mlx_lm.sample_utils import make_sampler
    with LOCK:
        if MODEL is None:
            # Resolver uses paths relative to the project directory.
            import os
            os.chdir(ROOT)
            MODEL, TOKENIZER = load(resolve_model_path("small"), adapter_path=str(ROOT / "artifacts/qwen05_lora"))
        mx.random.seed(42)
        prompt = TOKENIZER.apply_chat_template(messages_for({"input": model_input}), tokenize=False, add_generation_prompt=True)
        raw = generate(MODEL, TOKENIZER, prompt=prompt, max_tokens=768, sampler=make_sampler(temp=0.0), verbose=False)
    parsed, errors = parse_output(raw)
    return parsed, raw, errors


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
                                 "city": "London", "model": "Qwen2.5-0.5B-Instruct + LoRA"})
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
            else:
                parsed, raw, errors = extract(model_input)
            if parsed is None:
                return self.respond({"valid": False, "raw": raw, "errors": errors})
            date = body["date"]
            datetime.fromisoformat(date)
            assessment = rain_in_window(FORECAST, date + "T14:00", date + "T15:00")
            mode = body.get("weather_mode", "forecast")
            rain = True if mode == "rain" else False if mode == "dry" else assessment["rain"]
            plan = apply_constraints(model_input["reference_itinerary"], parsed, rain, PLACES)
            self.respond({"valid": True, "constraints": parsed["constraints"], "plan": plan,
                          "weather": assessment | {"rain": rain, "mode": mode}, "raw": raw,
                          "source": body.get("source", "live")})
        except Exception as error:
            self.respond({"error": str(error)}, 400)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    print(f"Open http://127.0.0.1:{args.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
