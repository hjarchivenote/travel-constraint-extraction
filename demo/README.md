# London, Replanned

A local interface for the project's NLP task: reference itinerary + English change request → structured conditions → illustrative plan edits.

## Start

From the repository root:

```bash
python3 demo/app.py
```

Open <http://127.0.0.1:8765>. **Saved validation run** works without model dependencies or downloads. Its four examples are actual recorded model predictions, with raw output and provenance in `saved_examples.json`; they are not corrected target labels. An edited request automatically selects **Live local model**.

For live inference on Apple Silicon, first install the root requirements and download the pinned small model:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
PYTHONPATH=src .venv/bin/python -m travel_constraints.download_models small
.venv/bin/python demo/app.py
```

The published adapter is in `artifacts/qwen05_lora/`. The first live request also loads the base model. No paid language-model API is used. Stop the server with Ctrl+C.

## Demonstration sequence

1. Use the first combined saved example; inspect its six extracted conditions and raw JSON.
2. Select **Rain simulation**: the outdoor walk becomes a book-cafe category.
3. Select **Dry simulation**: the original walk remains.
4. Select the ambiguous-time example: an unresolved deadline stays pending.
5. If the local model is installed, edit the text and run live extraction. Outputs may contain errors; schema failures are shown instead of repaired.

Forecast mode uses a timestamped London snapshot. **Refresh forecast** requests new Open-Meteo data; select a date within its coverage. Dates beyond coverage leave weather unknown. Simulation is explicitly labeled. Refresh updates the running server's memory, not the frozen snapshot or evaluation data.

## Scope

The planner demonstrates conditional application of extracted information. It does not optimize travel routes, verify opening hours, assert venue availability, or establish that a walking cap can be met. Nearby-place distance is straight-line distance. A book cafe is a requested category until a real venue is selected. Place and forecast attribution appear in the interface and source files.

![Application screenshot](../docs/images/demo.png)
