# Travel Constraint Extraction

Extract structured constraints from natural-language requests to change a travel itinerary, and compare a fine-tuned small Transformer with larger-model prompting.

**Status: the extraction contract, dataset generator, MLX training/inference pipeline, evaluation code, and London weather backend are implemented. Local development runs have started. Human annotation review and final held-out evaluation remain pending.**

## Project goal

Given a short reference itinerary and an English change request, identify the requirements that an itinerary adjustment should follow. The core task is NLP: extracting conditions, distinguishing hard constraints from soft preferences, and flagging requests that need clarification. The demonstration is set in central London and will use weather forecasts as contextual information for simple itinerary adjustments.

The project investigates whether task-specific fine-tuning can improve a small model's extraction performance, and how its accuracy and inference time compare with a larger model. Improvements are hypotheses to test; no final held-out performance results are available yet.

## Example task

**Reference itinerary:** Visit the National Gallery, have lunch, walk along the South Bank, and return to the hotel at 20:00. These times are illustrative reference settings.

**Change request:** "Keep the National Gallery visit. I must be back at the hotel by 19:00, and I would prefer less walking."

Expected information to extract:

| Condition | Value | Requirement type |
| --- | --- | --- |
| Place to keep | National Gallery | Hard constraint |
| Latest hotel return | 19:00 | Hard constraint |
| Walking preference | Less walking | Soft preference |
| Clarification needed | No | - |

The model returns structured JSON using the [output schema](src/travel_constraints/output_schema.json). The [shared contract](src/travel_constraints/contract.py) defines the extraction instructions. The example above illustrates the task; it is not a reported prediction.

## Scope

- English, single-turn change requests with a short reference itinerary.
- Central London, a one-day itinerary, and walking as the initial travel mode.
- Place inclusion and exclusion, time constraints, and walking limits or preferences.
- Hard constraints versus soft preferences, with an explicit clarification flag for ambiguous requests.
- A simple itinerary-adjustment demonstration using extracted conditions and weather-forecast context.

London place information and weather forecasts support the demonstration. Custom change requests and their reviewed constraint annotations will form the final NLP dataset. Weather-dependent actions carry an explicit `condition`, preserving both rain/no-rain alternatives. The weather backend retrieves a forecast and selects applicable conditions; a complete itinerary interface and routing system have not been implemented.

Planned demonstration sources are [OpenStreetMap](https://www.openstreetmap.org/copyright) for London place information and [Open-Meteo](https://open-meteo.com/) for weather forecasts. Published source-derived data will include the relevant attribution and license information. Reproducible experiments will use fixed weather snapshots; a live demonstration can request a fresh forecast and identify its retrieval time.

Live routing, booking, and real-time place information are outside the initial scope. The demonstration will use clearly identified reference itineraries rather than imply that fictional examples are current travel advice.

## Planned model comparison

| Approach | Model | Adaptation |
| --- | --- | --- |
| Small-model baseline | [Qwen2.5-0.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct) | Prompting without task-specific fine-tuning |
| Fine-tuned small model | Qwen2.5-0.5B-Instruct | Supervised fine-tuning with LoRA |
| Larger-model comparison | [Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct) | Few-shot prompting without fine-tuning |

All three approaches will use the same output schema and held-out test set. Prompts, model revisions, hardware, precision or quantization, and inference settings will be recorded to make the comparison interpretable.

## Planned dataset

The target is **400 custom examples in total**, including training, validation, and test examples. This is a collection target, not an established minimum or a guarantee of model performance.

The generator currently produces **400 synthetic candidates: 100 scenarios with four authored paraphrase templates per scenario**. The provisional split is 280 training, 40 validation, and 80 test candidates. These candidates are **not human-verified** and remain in the ignored `outputs/` directory. Templates are shared across scenario groups, so these data alone cannot establish generalization to independently written real-user requests. Test candidates remain reserved for independent human review and must not be used to choose prompts or training settings.

Each example will contain:

- A short reference itinerary set in London.
- An English change request.
- A manually verified structured target containing the requested constraints.

The annotation-review milestone is a **30–50-example pilot**. Initial development runs use automatically constructed candidates to verify execution, not to claim final accuracy. The generator covers explicit requirements, preferences, multiple conditions, negation, unresolved values, and conditional replacements. AI assistance and subsequent human review are recorded separately.

Splits are organized by scenario: a scenario and all its paraphrases stay in the same split. The current test candidates share the generator's template families with the other splits. Their final review and any rewriting will be completed without using model predictions, and they will not be used for prompt selection or training decisions. Synthetic test data will support conclusions about this controlled task; it will not establish performance on real travelers' requests.

## Planned evaluation

- **Constraint extraction precision, recall, and F1:** using matching and normalization rules defined before final evaluation.
- **Hard/soft classification accuracy:** on matched constraints, reported alongside extraction F1 so missed constraints remain visible.
- **JSON validity rate:** the proportion of outputs that satisfy the agreed schema.
- **Inference time:** with hardware, model precision, and measurement conditions documented.
- **Error analysis:** examples of missed conditions, incorrect values, requirement-type errors, and ambiguity handling.

Matching is one-to-one and ignores constraint ordering. Content matches include the condition, target, operator, value, unit, and scope; requirement strength and clarification are scored separately on matches. Strict JSON/schema failures receive no extracted constraints. Expected record IDs are checked so missing predictions cannot silently disappear from a reported score. Development checks must not be presented as final test results.

If time permits, a learning-curve experiment will compare different training-set sizes while keeping the validation and test sets fixed.

## Repository structure

```text
.
├── README.md
├── data/          # Dataset, provenance, annotation guidance, and splits
├── src/           # Extraction, training, inference, and evaluation code
├── experiments/   # Experiment settings, result tables, and error analysis
├── demo/          # A small interface demonstrating extraction and itinerary changes
└── docs/          # Project report, presentation, and supporting figures
```

## Roadmap

- [x] Create the repository structure and project overview.
- [x] Implement the output contract, extraction instructions, and one-to-one matching metrics.
- [x] Implement a reproducible generator for 400 candidates with scenario-disjoint splits.
- [x] Run local small-model inference and short LoRA training with saved adapter reload.
- [x] Run the quantized 7B comparison model on a development request.
- [x] Retrieve London forecasts and implement rain-conditional activation.
- [ ] Build and review the 30–50-example pilot.
- [ ] Complete human review and freeze the 400-example dataset and its splits.
- [ ] Run the small-model baseline, LoRA fine-tuning, and larger-model prompting comparison.
- [ ] Evaluate the models and analyze errors.
- [ ] Build the simple demonstration and add screenshots.
- [ ] Complete the report, presentation, and reproducibility instructions.

## Running the project

Tested environment: **Apple M2, 16 GB unified memory, macOS 26.5.2, Python 3.13.7**. The model runtime uses [MLX LM](https://github.com/ml-explore/mlx-lm), with [LoRA training](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/LORA.md) on the Apple GPU. The 7B comparison uses a pinned 4-bit MLX conversion; this precision difference must be reported when discussing speed or accuracy.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
PYTHONPATH=src .venv/bin/python -m travel_constraints.download_models small
PYTHONPATH=src .venv/bin/python -m travel_constraints.build_data
PYTHONPATH=src .venv/bin/python -m travel_constraints.train --model small
PYTHONPATH=src .venv/bin/python -m travel_constraints.infer --model small --records outputs/corpus/records.jsonl --ids outputs/corpus/pilot_training/validation_ids.json --limit 4 --output outputs/runtime/baseline.jsonl
PYTHONPATH=src .venv/bin/python -m travel_constraints.infer --model small --adapter outputs/runtime/pilot_adapter --records outputs/corpus/records.jsonl --ids outputs/corpus/pilot_training/validation_ids.json --limit 4 --output outputs/runtime/adapted.jsonl
PYTHONPATH=src .venv/bin/python -m travel_constraints.metrics --records outputs/corpus/records.jsonl --predictions outputs/runtime/adapted.jsonl --ids outputs/corpus/pilot_training/validation_ids.json --output outputs/runtime/adapted_metrics.json
PYTHONPATH=src .venv/bin/python -m travel_constraints.weather
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

The default training command is an execution pilot, not final training. It masks prompt tokens and updates LoRA adapters in the last four layers. The corpus builder refuses accidental overwrites, and the trainer checks splits, exported annotations, and token lengths. Final-mode training/evaluation requires reviewed labels. Models, adapters, generated candidates, and development outputs remain local. Only completed implementation units and reviewed artifacts are published.

The London weather backend requests ECMWF IFS 0.25° data. Rain/showers are preceding-hour totals; a 14:00–15:00 activity uses the bucket ending at 15:00. The demonstration uses a configurable 0.1 mm/hour rain-plus-showers threshold, conservatively considers overlapping partial hours, and preserves unknown weather as pending rather than assuming dry conditions. See [Open-Meteo's hourly variable definitions](https://open-meteo.com/en/docs).

## Licensing and model attribution

The two planned Qwen models are distributed under Apache 2.0; see the original [0.5B license](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct/blob/main/LICENSE) and [7B license](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/blob/main/LICENSE). Any redistributed model derivatives will preserve the required license and attribution notices and identify modifications.

Original code, dataset, and documentation licensing will be specified before those artifacts are released for reuse. Base-model weights will be referenced through their original repositories. Any released LoRA adapters will include the base-model revision and training details.

## Author and context

Hyojin Lee · Recent Areas of AI semester project · 2026

This repository records the project as it develops. Dataset sizes, evaluation results, and completed features will be updated only when the corresponding work has been completed.
