# Trained LoRA adapter

Base: Qwen2.5-0.5B-Instruct at pinned revision `7ae557604adf67be50417f59c2c2f167def9a775`.

The 2.9 MB adapter was trained on 280 AI-reviewed synthetic requests, with 40 validation requests and no test examples, using LoRA rank 8 in the last four layers. All 840 CPU training steps completed. See [training details](../../experiments/training_run.json).

Human annotation verification has not been performed. This model is a controlled research prototype, not a verified travel-planning service.

Held-out synthetic test: content F1 **0.795**, full-record accuracy **57/80**, schema validity **97.5%**. See [all approaches and limitations](../../experiments/results/comparison.json) and [actual failures](../../experiments/results/error_analysis.json). Priority accuracy is conditional on matched content; missed constraints still reduce recall. These results do not establish accuracy on real user requests.

Use with `mlx_lm.load(base_model_path, adapter_path="artifacts/qwen05_lora")`. Original weights are downloaded separately through the pinned model downloader. Apache 2.0 notices are included.
