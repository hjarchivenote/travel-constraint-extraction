# Travel Constraint Extraction

Extract structured constraints from natural-language requests to change a travel itinerary, and compare a fine-tuned small Transformer with larger-model prompting.

**Status: repository setup complete; dataset construction, model training, and evaluation have not started.**

## Project goal

Given a short reference itinerary and an English change request, identify the requirements that an itinerary adjustment should follow. The core task is NLP: extracting conditions, distinguishing hard constraints from soft preferences, and flagging requests that need clarification.

The project investigates whether task-specific fine-tuning can improve a small model's extraction performance, and how its accuracy and inference time compare with a larger model. Improvements are hypotheses to test; no performance results are available yet.

## Example task

**Reference itinerary:** Visit the Colosseum, have lunch, visit the Pantheon, and return to the hotel at 20:00.

**Change request:** "Keep the Colosseum visit. I must be back at the hotel by 19:00, and I would prefer less walking."

Expected information to extract:

| Condition | Value | Requirement type |
| --- | --- | --- |
| Place to keep | Colosseum | Hard constraint |
| Latest hotel return | 19:00 | Hard constraint |
| Walking preference | Less walking | Soft preference |
| Clarification needed | No | — |

The model will return structured JSON. The exact schema and annotation rules will be finalized before dataset construction. This example illustrates the intended task; it is not a model prediction.

## Scope

- English, single-turn change requests with a short reference itinerary.
- Place inclusion and exclusion, time constraints, and walking limits or preferences.
- Hard constraints versus soft preferences, with an explicit clarification flag for ambiguous requests.
- A simple itinerary-adjustment demonstration using the extracted conditions.

Live routing, booking, and real-time place information are outside the initial scope. The demonstration will use clearly identified reference itineraries rather than imply that fictional examples are current travel advice.

## Planned model comparison

| Approach | Model | Adaptation |
| --- | --- | --- |
| Small-model baseline | [Qwen2.5-0.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct) | Prompting without task-specific fine-tuning |
| Fine-tuned small model | Qwen2.5-0.5B-Instruct | Supervised fine-tuning with LoRA |
| Larger-model comparison | [Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct) | Few-shot prompting without fine-tuning |

All three approaches will use the same output schema and held-out test set. Prompts, model revisions, hardware, precision or quantization, and inference settings will be recorded to make the comparison interpretable.

## Planned dataset

The initial target is approximately **400 custom examples in total**, including training, validation, and test examples. This is an initial collection target, not an established minimum or a guarantee of model performance.

Each example will contain:

- A short reference itinerary.
- An English change request.
- A manually verified structured target containing the requested constraints.

The first milestone is a **30–50-example pilot** to check annotation consistency and the training workflow. Examples will cover explicit requirements, preferences, multiple conditions, negation, and ambiguity. If AI assists with drafting examples or annotations, that assistance and the manual review process will be documented.

Splits will be organized by scenario: a scenario and all its paraphrases must stay in the same split. Test scenarios will be authored and reviewed independently from training examples, and will not be used for prompt selection or training decisions. Synthetic test data will support conclusions about this controlled task; it will not establish performance on real travelers' requests.

## Planned evaluation

- **Constraint extraction precision, recall, and F1:** using matching and normalization rules defined before final evaluation.
- **Hard/soft classification accuracy:** on matched constraints, reported alongside extraction F1 so missed constraints remain visible.
- **JSON validity rate:** the proportion of outputs that satisfy the agreed schema.
- **Inference time:** with hardware, model precision, and measurement conditions documented.
- **Error analysis:** examples of missed conditions, incorrect values, requirement-type errors, and ambiguity handling.

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
- [ ] Define the JSON schema, annotation rules, and evaluation matching rules.
- [ ] Build and review the 30–50-example pilot.
- [ ] Verify model inference and a short LoRA training run.
- [ ] Expand the dataset and freeze scenario-based splits.
- [ ] Run the small-model baseline, LoRA fine-tuning, and larger-model prompting comparison.
- [ ] Evaluate the models and analyze errors.
- [ ] Build the simple demonstration and add screenshots.
- [ ] Complete the report, presentation, and reproducibility instructions.

## Running the project

No executable pipeline or installation instructions are available yet. Dependencies and commands will be added after the first verified model run.

## Licensing and model attribution

The two planned Qwen models are distributed under Apache 2.0; see the original [0.5B license](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct/blob/main/LICENSE) and [7B license](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/blob/main/LICENSE). Any redistributed model derivatives will preserve the required license and attribution notices and identify modifications.

Original code, dataset, and documentation licensing will be specified before those artifacts are released for reuse. Base-model weights will be referenced through their original repositories. Any released LoRA adapters will include the base-model revision and training details.

## Author and context

Hyojin Lee · Recent Areas of AI semester project · 2026

This repository records the project as it develops. Dataset sizes, evaluation results, and completed features will be updated only when the corresponding work has been completed.
