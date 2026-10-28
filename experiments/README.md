# Experiments

Planned home for experiment configurations, model revisions, prompts, reproducibility details, metrics, and error analysis.

The comparison will include the untuned Qwen2.5-0.5B-Instruct model, its LoRA-fine-tuned version, and few-shot prompting of Qwen2.5-7B-Instruct on the same held-out test set.

**Current status:** local execution checks and short development training runs have been performed. Logs and predictions are kept in ignored `outputs/runtime/`. No final held-out test experiment has been run or published. The 80 test candidates remain reserved for human review and final evaluation.

Those development runs used corpus v1. The AI-reviewed v2 working corpus is in `outputs/corpus_reviewed_v2/`; no v2 training or model evaluation has been performed. Do not mix the old predictions with v2 annotations or report them as v2 scores.
