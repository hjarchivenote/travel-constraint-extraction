"""Replay saved raw predictions through the live routing rule, without model calls."""

import argparse
import hashlib
import json
from pathlib import Path

from .contract import SCHEMA_PATH
from .extraction import extract_with_fallback
from .metrics import summarize


def read_rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def replay(records, primary_predictions, fallback_predictions):
    expected = {r["id"] for r in records}
    sources = []
    schema_sha = sha(SCHEMA_PATH)
    for predictions in (primary_predictions, fallback_predictions):
        by_id = {p["id"]: p for p in predictions}
        if len(by_id) != len(predictions) or set(by_id) != expected:
            raise ValueError("Both complete prediction sets must match the reference IDs exactly")
        for record in records:
            prediction = by_id[record["id"]]
            fingerprint = hashlib.sha256(json.dumps(record["input"], sort_keys=True).encode()).hexdigest()
            if prediction["record_input_sha256"] != fingerprint:
                raise ValueError("Cached prediction input differs from its reference input")
            if prediction["schema_sha256"] != schema_sha or prediction["few_shot_examples"] != []:
                raise ValueError("Replay requires the same schema and zero-shot inference on both models")
        sources.append(by_id)
    primary, fallback = sources
    routed = []
    for record in records:
        first, second = primary[record["id"]], fallback[record["id"]]
        # Reference targets are not passed to this routing function.
        result = extract_with_fallback(record["input"], lambda _: first["raw_output"],
                                       lambda _: second["raw_output"])
        seconds = first["inference_seconds"] + (second["inference_seconds"] if result["fallback_used"] else 0)
        routed.append({"id": record["id"], **result, "inference_seconds": seconds,
                       "latency_kind": "sum of recorded generation times; excludes model-switch overhead"})
    return routed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", required=True)
    parser.add_argument("--primary", required=True)
    parser.add_argument("--fallback", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--split", choices=["validation", "test"], default="validation")
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise SystemExit("Use a new output directory; raw or prior results are never overwritten")
    records = [r for r in read_rows(args.records) if r["split"] == args.split]
    primary, fallback = read_rows(args.primary), read_rows(args.fallback)
    routed = replay(records, primary, fallback)
    metrics = {"original_model": summarize(records, fallback),
               "raw_primary_model": summarize(records, primary),
               "routed_system": summarize(records, routed)}
    metrics["fallback_calls"] = sum(r["fallback_used"] for r in routed)
    metrics["both_models_invalid"] = sum(r["parsed_output"] is None for r in routed)
    axes = ("exact_record_accuracy", "f1", "schema_validity_rate")
    metrics["no_regression_vs_original"] = all(
        metrics["routed_system"][a] >= metrics["original_model"][a] for a in axes)
    metrics["provenance"] = {"mode": "cached raw-prediction replay; zero new model calls",
        "split": args.split, "record_sha256": sha(args.records), "primary_sha256": sha(args.primary),
        "fallback_sha256": sha(args.fallback), "schema_sha256": sha(SCHEMA_PATH),
        "selection_rule": "JSON/schema invalidity or three identical complete constraints triggers fallback; no gold targets used",
        "raw_outputs_repaired": False, "reference_targets_changed": False,
        "latency": "Replayed generation-time estimate, not a live latency benchmark",
        "limitation": "Routing was developed on these validation sets; results are not fresh test evidence"}
    output.mkdir(parents=True)
    (output / "predictions.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in routed))
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps({k: metrics[k] for k in ["fallback_calls", "both_models_invalid", "no_regression_vs_original"]}))
    for label in ("original_model", "raw_primary_model", "routed_system"):
        print(label, json.dumps({a: metrics[label][a] for a in axes}))


if __name__ == "__main__":
    main()
