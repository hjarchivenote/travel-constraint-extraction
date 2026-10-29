# Experiments

`protocol.json` freezes the dataset/schema/system-prompt hashes, 80 held-out IDs, pinned model revisions, generation settings, and three approaches. It was written before final test inference. `training_run.json` records the completed 840-step CPU LoRA run and saved-weight verification.

`results/` retains raw model outputs, per-record provenance, per-family metrics, reference-group bootstrap intervals, the comparison summary, and every non-exact prediction in the error analysis. Schema-invalid outputs are not repaired. All three approaches use the same held-out set. Labels are **AI-reviewed synthetic, with zero human-verified records**; metrics do not establish generalization to real users.

The 7B comparison uses 4-bit weights and two training demonstrations; small-model runs use bfloat16 weights and zero-shot prompts. Those differences limit causal interpretation. Generation times include prompt processing and the first request after load. Full raw paths in prediction records are historical execution provenance, not paths required on another computer.

The root README gives commands to recompute scores from saved outputs and to run a separate reproduction with the published adapter. New measurements go to `outputs/reproduction/` so that the submitted results are preserved. The runner refuses partial prediction files rather than silently rerunning selected cases.
