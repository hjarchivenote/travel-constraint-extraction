"""Run LoRA with recorded settings and no access to held-out test examples."""

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from .download_models import resolve_model_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--data", default="outputs/corpus/pilot_training")
    parser.add_argument("--records", default="outputs/corpus/records.jsonl")
    parser.add_argument("--adapter", default="outputs/runtime/pilot_adapter")
    parser.add_argument("--iters", type=int, default=20)
    parser.add_argument("--layers", type=int, default=4)
    parser.add_argument("--max-seq-length", type=int, default=1024)
    parser.add_argument("--learning-rate", type=float, default=0.0001)
    parser.add_argument("--device", choices=["gpu", "cpu"], default="gpu")
    parser.add_argument("--disable-compile", action="store_true",
                        help="Disable MLX compilation for a Metal-error diagnostic run")
    parser.add_argument("--resume-adapter-file")
    parser.add_argument("--save-every", type=int, default=20)
    parser.add_argument("--purpose", choices=["pilot", "final"], default="pilot")
    args = parser.parse_args()
    args.model = resolve_model_path(args.model)
    data = Path(args.data)
    records = {row["id"]: row for row in map(json.loads, Path(args.records).read_text().splitlines())}
    selections = {split: json.loads((data / f"{split}_ids.json").read_text())
                  for split in ("train", "validation")}
    if not selections["train"] or not selections["validation"]:
        raise SystemExit("Both training and validation examples are required.")
    groups = {}
    for split, ids in selections.items():
        if any(records[record_id]["split"] != split for record_id in ids):
            raise SystemExit("Dataset split mismatch; test examples must never enter training.")
        groups[split] = {records[record_id]["scenario_id"] for record_id in ids}
        filename = "train.jsonl" if split == "train" else "valid.jsonl"
        exported = [json.loads(line) for line in (data / filename).read_text().splitlines() if line.strip()]
        if len(exported) != len(ids):
            raise SystemExit("Exported training rows and record IDs do not match.")
        for record_id, row in zip(ids, exported):
            if json.loads(row["messages"][-1]["content"]) != records[record_id]["target"]:
                raise SystemExit("Exported annotations are stale; export the reviewed targets again.")
            if json.loads(row["messages"][-2]["content"]) != records[record_id]["input"]:
                raise SystemExit("Exported model inputs do not match their record IDs.")
        if args.purpose == "final" and any(not records[record_id]["metadata"]["human_reviewed"] for record_id in ids):
            raise SystemExit("Final training requires reviewed annotations. Use pilot mode only for development checks.")
    if groups["train"] & groups["validation"]:
        raise SystemExit("Training and validation share a scenario group.")
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True)
    max_observed_tokens = 0
    for filename in ("train.jsonl", "valid.jsonl"):
        for line in (data / filename).read_text().splitlines():
            messages = json.loads(line)["messages"]
            max_observed_tokens = max(max_observed_tokens,
                                      len(tokenizer.apply_chat_template(messages, return_dict=False)))
    if max_observed_tokens > args.max_seq_length:
        raise SystemExit(f"An example needs {max_observed_tokens} tokens; refusing to silently truncate at {args.max_seq_length}.")
    adapter = Path(args.adapter)
    if adapter.exists() and any(adapter.iterdir()):
        raise SystemExit("Adapter directory is not empty; use a distinct run directory.")
    adapter.mkdir(parents=True, exist_ok=True)
    launcher = [sys.executable, "-m", "mlx_lm"]
    if args.device == "cpu":
        launcher = [sys.executable, "-c", "import runpy; import mlx.core as mx; "
                    "mx.set_default_device(mx.cpu); runpy.run_module('mlx_lm', run_name='__main__')"]
    command = launcher + ["lora", "--model", args.model,
               "--train", "--data", str(data), "--adapter-path", str(adapter),
               "--iters", str(args.iters), "--num-layers", str(args.layers),
               "--batch-size", "1", "--learning-rate", str(args.learning_rate),
               "--max-seq-length", str(args.max_seq_length), "--mask-prompt",
               "--steps-per-report", "1", "--steps-per-eval", str(args.iters),
               "--val-batches", "2", "--save-every", str(args.save_every), "--seed", "42"]
    if args.resume_adapter_file:
        if not Path(args.resume_adapter_file).is_file():
            raise SystemExit("Resume adapter file does not exist.")
        command.extend(["--resume-adapter-file", args.resume_adapter_file])
    environment = os.environ | {"PYTHONUNBUFFERED": "1", "HF_HUB_DISABLE_PROGRESS_BARS": "1"}
    if args.disable_compile:
        environment["MLX_DISABLE_COMPILE"] = "1"
    manifest = {"purpose": args.purpose, "command": command, "iterations": args.iters, "device": args.device,
                "compilation_disabled": "MLX_DISABLE_COMPILE" in environment,
                "mlx_disable_compile_env": environment.get("MLX_DISABLE_COMPILE"),
                "max_observed_example_tokens": max_observed_tokens,
                "train_records": len(selections["train"]), "validation_records": len(selections["validation"]),
                "test_records_used": 0, "annotation_review_complete": args.purpose == "final",
                "mlx_lm_version": importlib.metadata.version("mlx-lm"),
                "resumed_adapter": args.resume_adapter_file,
                "resume_sha256": hashlib.sha256(Path(args.resume_adapter_file).read_bytes()).hexdigest() if args.resume_adapter_file else None,
                "data_sha256": {name: hashlib.sha256((data / name).read_bytes()).hexdigest()
                                for name in ("train.jsonl", "valid.jsonl")},
                "record_ids": selections}
    manifest_path = adapter / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    started = time.perf_counter()
    with (adapter / "training.log").open("w") as log:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, bufsize=1, env=environment)
        for line in process.stdout:
            log.write(line)
            log.flush()
            print(line, end="", flush=True)
        return_code = process.wait()
    manifest.update({"elapsed_seconds": round(time.perf_counter() - started, 3), "exit_code": return_code,
                     "adapter_saved": (adapter / "adapters.safetensors").is_file()})
    manifest_path.write_text(json.dumps(manifest, indent=2))
    if return_code or not manifest["adapter_saved"]:
        raise SystemExit(return_code or "Training did not produce adapter weights.")
    print(json.dumps({key: manifest[key] for key in ("purpose", "iterations", "elapsed_seconds", "adapter_saved", "test_records_used")}))


if __name__ == "__main__":
    main()
