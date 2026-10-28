"""Run reproducible MLX inference and retain raw, uncorrected model output."""

import argparse
import hashlib
import importlib.metadata
import json
import platform
import time
from pathlib import Path

from .contract import messages_for, parse_output
from .download_models import resolve_model_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Pinned local model snapshot")
    parser.add_argument("--records", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--split", default="validation")
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--family")
    parser.add_argument("--ids", help="Optional JSON list of development record IDs")
    parser.add_argument("--adapter")
    parser.add_argument("--few-shot", type=int, default=0)
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--purpose", choices=["pilot", "final"], default="pilot")
    args = parser.parse_args()
    if args.split == "test" and args.purpose != "final":
        raise SystemExit("Held-out test examples cannot be used for development runs.")
    if args.few_shot < 0 or args.limit <= 0:
        raise SystemExit("Few-shot count must be nonnegative and the record limit must be positive.")
    args.model = resolve_model_path(args.model)

    import mlx.core as mx
    from mlx_lm import generate, load
    from mlx_lm.sample_utils import make_sampler

    records = [json.loads(line) for line in Path(args.records).read_text().splitlines() if line.strip()]
    selected_ids = set(json.loads(Path(args.ids).read_text())) if args.ids else None
    selected = [record for record in records if record["split"] == args.split
                and (args.family is None or record["family"] == args.family)
                and (selected_ids is None or record["id"] in selected_ids)][:args.limit]
    if not selected:
        raise SystemExit("No records match the requested split.")
    if args.purpose == "final" and any(not record["metadata"]["human_reviewed"] for record in selected):
        raise SystemExit("Final evaluation requires reviewed reference annotations.")
    train = [record for record in records if record["split"] == "train"]
    preferred = [next((record for record in train if record["family"] == family), None)
                 for family in ("combined", "walking_limit")] if args.few_shot else []
    preferred = [record for record in preferred if record is not None]
    demonstrations = (preferred + [record for record in train if record not in preferred])[:args.few_shot]
    if args.purpose == "final" and any(not record["metadata"]["human_reviewed"] for record in demonstrations):
        raise SystemExit("Final prompting requires reviewed few-shot demonstrations.")
    mx.random.seed(42)
    started = time.perf_counter()
    model, tokenizer = load(args.model, adapter_path=args.adapter)
    load_seconds = time.perf_counter() - started
    model_config = json.loads((Path(args.model) / "config.json").read_text())
    adapter_sha256 = hashlib.sha256((Path(args.adapter) / "adapters.safetensors").read_bytes()).hexdigest() if args.adapter else None
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as handle:
        for index, record in enumerate(selected):
            prompt = tokenizer.apply_chat_template(
                messages_for(record, demonstrations), tokenize=False, add_generation_prompt=True
            )
            started = time.perf_counter()
            raw = generate(model, tokenizer, prompt=prompt, max_tokens=args.max_tokens,
                           sampler=make_sampler(temp=0.0), verbose=False)
            elapsed = time.perf_counter() - started
            parsed, errors = parse_output(raw)
            result = {
                "id": record["id"], "scenario_id": record["scenario_id"], "split": args.split,
                "model_path": args.model, "adapter_path": args.adapter,
                "adapter_sha256": adapter_sha256,
                "model_revision": Path(args.model).name,
                "quantization": model_config.get("quantization", model_config.get("quantization_config")),
                "weight_dtype": model_config.get("dtype", model_config.get("torch_dtype")),
                "few_shot_examples": [example["id"] for example in demonstrations],
                "raw_output": raw, "parsed_output": parsed, "validation_errors": errors,
                "inference_seconds": round(elapsed, 4), "load_seconds": round(load_seconds, 4),
                "first_generation_after_load": index == 0,
                "max_tokens": args.max_tokens, "temperature": 0.0, "seed": 42,
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "record_input_sha256": hashlib.sha256(json.dumps(record["input"], sort_keys=True).encode()).hexdigest(),
                "schema_sha256": hashlib.sha256(Path(__file__).with_name("output_schema.json").read_bytes()).hexdigest(),
                "output_tokens_retokenized": len(tokenizer.encode(raw, add_special_tokens=False)),
                "mlx_lm_version": importlib.metadata.version("mlx-lm"),
                "platform": platform.platform(),
                "purpose": args.purpose,
            }
            handle.write(json.dumps(result, ensure_ascii=False) + "\n")
            handle.flush()
            print(json.dumps({"id": record["id"], "seconds": round(elapsed, 2),
                              "valid": parsed is not None, "raw": raw[:200]}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
