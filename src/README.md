# Source code

The `travel_constraints` package implements the first executable project pipeline:

- `contract.py` and `output_schema.json`: structured output, prompts, and strict validation.
- `build_data.py`: 400 synthetic candidates, scenario-based splitting, and development training export.
- `request_wording.py`: separate authored validation/test wording pools.
- `audit_data.py`: checks annotation values, unresolved fields, weather branches, and cross-split duplicates; does not grant human approval.
- `download_models.py`: pinned model snapshots.
- `train.py`: recorded LoRA runs, split checks, and prompt masking.
- `infer.py`: raw predictions, adapters, few-shot examples, and latency records.
- `metrics.py`: one-to-one extraction matching and separate label accuracy.
- `weather.py`: London forecasts and conditional activation.

See the root README for commands. Human dataset review, final evaluation, and the presentation remain outstanding.
