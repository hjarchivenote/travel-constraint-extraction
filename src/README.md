# Source code

The `travel_constraints` package implements the first executable project pipeline:

- `contract.py` and `output_schema.json`: structured output, prompts, and strict validation.
- `build_data.py`: 400 synthetic candidates, scenario-based splitting, and development training export.
- `download_models.py`: pinned model snapshots.
- `train.py`: recorded LoRA runs, split checks, and prompt masking.
- `infer.py`: raw predictions, adapters, few-shot examples, and latency records.
- `metrics.py`: one-to-one extraction matching and separate label accuracy.
- `weather.py`: London forecasts and conditional activation.

See the root README for commands. Human dataset review, final evaluation, and the presentation remain outstanding.
