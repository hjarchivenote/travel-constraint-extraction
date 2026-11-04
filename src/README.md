# Source code

- `travel_constraints/contract.py` and `output_schema.json`: prompt, structured output and validation.
- `travel_constraints/extraction.py`: local model inference, schema checks and fallback.
- `travel_constraints/evidence_guard.py` and `coverage.py`: request consistency checks and targeted retries.
- `travel_constraints/metrics.py`: content matching and exact request scoring.
- `travel_constraints/planner.py` and `weather.py`: illustrative itinerary edits and forecast context.

See the [root README](../README.md) for the current demo and score reproduction commands.
