"""Run the frozen three-model comparison; retain every raw model response."""

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "src"))
from travel_constraints.metrics import summarize, score_one
from travel_constraints.contract import parse_output, SCHEMA_PATH, SYSTEM_PROMPT


def main(output_dir="experiments/results", runtime_dir="outputs/final_comparison"):
    protocol = json.loads(Path("experiments/protocol.json").read_text())
    source = Path(protocol["dataset_path"])
    assert hashlib.sha256(source.read_bytes()).hexdigest() == protocol["dataset_sha256"]
    assert hashlib.sha256(SCHEMA_PATH.read_bytes()).hexdigest() == protocol["schema_sha256"]
    assert hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest() == protocol["system_prompt_sha256"]
    records = [json.loads(line) for line in source.read_text().splitlines()]
    test = [r for r in records if r["split"] == "test"]
    expected_ids = set(protocol["test_ids"])
    assert len(test) == 80 and {r["id"] for r in test} == expected_ids
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    runtime = Path(runtime_dir)
    runtime.mkdir(parents=True, exist_ok=True)
    state = {"state": "running", "started_at_utc": datetime.now(timezone.utc).isoformat(),
             "dataset_sha256": protocol["dataset_sha256"], "completed_models": []}
    def save():
        (runtime / "status.json").write_text(json.dumps(state, indent=2) + "\n")
    save()
    all_metrics, all_errors = {}, {}
    for approach in protocol["approaches"]:
        tag = approach["id"]
        state["current_model"] = tag
        save()
        predictions_path = output / f"{tag}.jsonl"
        adapter = Path(approach["adapter"]) if approach.get("adapter") else None
        if adapter and not adapter.is_dir():
            adapter = Path("artifacts/qwen05_lora")
        expected_adapter_sha = hashlib.sha256((adapter / "adapters.safetensors").read_bytes()).hexdigest() if adapter else None
        if adapter:
            trained_sha = json.loads(Path("experiments/training_run.json").read_text())["adapter_sha256"]
            assert expected_adapter_sha == trained_sha, "Adapter differs from the submitted training artifact."
        if predictions_path.exists():
            existing = [json.loads(line) for line in predictions_path.read_text().splitlines()]
            if {p["id"] for p in existing} != expected_ids or len(existing) != 80:
                raise RuntimeError(f"Partial predictions retained at {predictions_path}; inspect before restarting.")
        else:
            command = [sys.executable, "-m", "travel_constraints.infer", "--model", approach["model"],
                       "--records", str(source), "--split", "test", "--limit", "80",
                       "--max-tokens", str(protocol["max_tokens"]), "--few-shot", str(approach["few_shot"]),
                       "--purpose", "final", "--accept-ai-reviewed",
                       "--expected-dataset-sha256", protocol["dataset_sha256"],
                       "--output", str(predictions_path)]
            if adapter:
                command += ["--adapter", str(adapter)]
            with (runtime / f"{tag}.log").open("w") as log:
                subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT,
                               env=os.environ | {"PYTHONPATH": "src", "PYTHONUNBUFFERED": "1"})
        predictions = [json.loads(line) for line in predictions_path.read_text().splitlines()]
        reference_by_id = {r["id"]: r for r in test}
        train_ids = {r["id"] for r in records if r["split"] == "train"}
        for pred in predictions:
            assert pred["dataset_sha256"] == protocol["dataset_sha256"]
            assert pred["schema_sha256"] == protocol["schema_sha256"]
            assert pred["model_revision"] == protocol["model_revisions"][approach["model"]]["revision"]
            assert pred["adapter_sha256"] == expected_adapter_sha
            assert pred["max_tokens"] == protocol["max_tokens"] and pred["temperature"] == 0 and pred["seed"] == 42
            assert len(pred["few_shot_examples"]) == approach["few_shot"] and set(pred["few_shot_examples"]) <= train_ids
            expected_input_sha = hashlib.sha256(json.dumps(reference_by_id[pred["id"]]["input"], sort_keys=True).encode()).hexdigest()
            assert pred["record_input_sha256"] == expected_input_sha
        metrics = summarize(test, predictions)
        by_id = {p["id"]: p for p in predictions}
        families = {}
        groups = defaultdict(lambda: [0, 0, 0, 0, 0])
        errors = []
        for record in test:
            pred = by_id[record["id"]]
            parsed = parse_output(pred["raw_output"])[0]
            score = score_one(record["target"], parsed)
            group = groups[record["scenario_id"]]
            for i, key in enumerate(("tp", "fp", "fn")):
                group[i] += score[key]
            group[3] += score["exact"]
            group[4] += 1
            if not score["exact"]:
                errors.append({"id": record["id"], "family": record["family"],
                               "input": record["input"], "expected": record["target"],
                               "prediction": parsed, "validation_errors": pred["validation_errors"],
                               "score": score})
        for family in dict.fromkeys(r["family"] for r in test):
            subset = [r for r in test if r["family"] == family]
            families[family] = summarize(subset, [by_id[r["id"]] for r in subset])
        rng = random.Random(42)
        clustered = list(groups.values())
        bootstrap_f1 = []
        for _ in range(2000):
            sample = rng.choices(clustered, k=len(clustered))
            tp, fp, fn = (sum(g[i] for g in sample) for i in range(3))
            bootstrap_f1.append(2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0)
        bootstrap_f1.sort()
        metrics.update({"f1_cluster_bootstrap_95_interval": [bootstrap_f1[49], bootstrap_f1[1949]],
                        "bootstrap_unit": "reference scenario (four paraphrases kept together)",
                        "bootstrap_resamples": 2000, "by_family": families})
        all_metrics[tag] = metrics
        all_errors[tag] = errors
        (output / f"{tag}_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
        state["completed_models"].append(tag)
        save()
    summary = {"dataset_sha256": protocol["dataset_sha256"], "records_per_model": 80,
               "annotation_review": protocol["annotation_review"], "metrics": all_metrics,
               "quantization_caveat": "Small models use original bfloat16 weights; the 7B model uses a 4-bit MLX conversion. Capacity, quantization and prompting differ.",
               "latency_policy": "Generation wall time includes prompt processing and the first generation after load; load time is separate. No speed-only claim.",
               "finished_at_utc": datetime.now(timezone.utc).isoformat()}
    (output / "comparison.json").write_text(json.dumps(summary, indent=2) + "\n")
    (output / "error_analysis.json").write_text(json.dumps(all_errors, indent=2) + "\n")
    state.update({"state": "complete", "finished_at_utc": summary["finished_at_utc"]})
    save()
    print(json.dumps({"state": "complete", "models": list(all_metrics)}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="experiments/results", help="Use a new directory to retain separate reproduction measurements")
    parser.add_argument("--runtime", default="outputs/final_comparison")
    args = parser.parse_args()
    try:
        main(args.output, args.runtime)
    except Exception as error:
        status = Path(args.runtime) / "status.json"
        state = json.loads(status.read_text()) if status.exists() else {}
        state.update({"state": "failed", "error": str(error)})
        status.parent.mkdir(parents=True, exist_ok=True)
        status.write_text(json.dumps(state, indent=2) + "\n")
        raise
