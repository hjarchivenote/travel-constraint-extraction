# Data

Planned home for the custom travel change-request dataset, finalized annotation guidelines, provenance records, and scenario-based train/validation/test splits.

**Current status:** the local v2 corpus has completed first-pass AI review and all-record consistency checks. Its 400 records in 100 reference-scenario groups remain split 280/40/80. Human review is pending and no human approval is inferred. The [review record](ai_review_v2.json) distinguishes AI review from human review.

Only completed, reviewed NLP artifacts will be published here. The executable [output schema](../src/travel_constraints/output_schema.json) and [prompt contract](../src/travel_constraints/contract.py) define the current format. Generated candidates remain in ignored `outputs/corpus/`; none are marked human-reviewed. Keep each scenario and its paraphrases in the same split and record any subsequent manual changes. Define a dataset license before release for reuse.

The reviewed working copy is `outputs/corpus_reviewed_v2/records.jsonl`; v1 is preserved unchanged in `outputs/corpus/`. The v2 directory contains the AI-review metadata, audit results, full training export in `training/`, and small development export in `pilot_training/`. Use explicit v2 record and data paths for subsequent training. Existing model runs belong to v1 and are not v2 results.

V2 removes 37 groups of identical request sentences that previously crossed splits, breaks the association between gallery name and hard/soft labels, and corrects awkward lunch wording. It has 400 distinct model inputs and 252 distinct request texts; within-split repetition and shared semantic intents remain disclosed limitations. No model training or prediction was used to make these corrections.

The NLP dataset consists of custom requests and target annotations. London place information and weather-forecast records are supporting demonstration data and will be documented with their own sources and applicable terms when used.

[reference/london_places.json](reference/london_places.json) contains six static reference locations extracted from the previously audited OpenStreetMap snapshot. It includes ODbL attribution, source, dates, and coordinate limitations. This file is not the NLP training dataset and does not assert current opening hours or booking availability.
