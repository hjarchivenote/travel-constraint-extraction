# Experiments

## Final test: 100 requests

[Final protocol](final100/protocol.json) pins the model revisions, exact test IDs, settings, and code and prediction checksums. The earlier and improved 1.5B LoRA adapters used identical test inputs. Scoring separates primary outputs from the complete validation, fallback and retry pipeline.

After installing `jsonschema`, run `python experiments/final100/recompute.py` from the repository root. It checks the dataset and prediction hashes and reproduces both sets of results from the saved outputs. It does not run inference.

The improved system fully matched 82 of 100 requests. One remaining error, `expanded_test_0078`, assigned a 73-minute walking allowance to each leg even though the request explicitly left the scope undecided. See [report evidence](final100/report_evidence.json) for examples and family counts. The tests are AI-authored synthetic requests and targets with no human review.

## Original test: 80 requests

This separate study uses the [original corpus](../data/travel_requests.jsonl) and the [original protocol](protocol.json). It compares a zero-shot 0.5B baseline, its LoRA version, and a 4-bit 7B model with two training examples. All three used the same 80 inputs and strict parsing without repair. Content F1 was 0.000, 0.795, and 0.782 respectively. Different model size, precision, and prompts limit interpretation. These scores must not be compared directly with the 100-request results.

[Original results and predictions](results/) include per-family metrics and bootstrap intervals. Historical model locations in the original prediction rows are recorded as repository ID and revision for portability. Predictions and scores are unchanged. The legacy rerun entry point writes separately from the recorded results.
