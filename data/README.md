# Data

Home for the custom travel change-request dataset design, annotation guidelines, provenance records, and future scenario-based train/validation/test splits.

**Current status:** draft guidelines and one illustrative record have been added. The illustration is pending human review and is not counted as pilot, training, validation, or test data. The initial collection target remains approximately 400 examples in total, starting with a 30–50-example pilot.

## Current files

- [annotation_guidelines.md](annotation_guidelines.md): the working rules and field definitions discussed during project design.
- [examples/example_001.json](examples/example_001.json): one fictional reference itinerary and English request paired with a draft target JSON.

Each future dataset record will separate model input from the expected output. Only `input` is given to the model. `target` is the expected answer used for supervised training and evaluation. IDs and provenance metadata support review and scenario-based splitting; they are not part of the requested model output.

Before collecting the pilot, finalize the output schema and annotation rules. Record any AI assistance, manually verify targets, and keep each scenario and its paraphrases in the same split. Define a dataset license before release for reuse.
