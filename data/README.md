# Data

Planned home for the custom travel change-request dataset, finalized annotation guidelines, provenance records, and scenario-based train/validation/test splits.

**Current status:** no completed NLP dataset is published. The local generator produces 400 candidates in 100 scenario groups, provisionally split 280/40/80. Human review is pending. A 30–50-example annotation pilot precedes freezing the final dataset.

Only completed, reviewed NLP artifacts will be published here. The executable [output schema](../src/travel_constraints/output_schema.json) and [prompt contract](../src/travel_constraints/contract.py) define the current format. Generated candidates remain in ignored `outputs/corpus/`; none are marked human-reviewed. Keep each scenario and its paraphrases in the same split and record any subsequent manual changes. Define a dataset license before release for reuse.

The NLP dataset consists of custom requests and target annotations. London place information and weather-forecast records are supporting demonstration data and will be documented with their own sources and applicable terms when used.

[reference/london_places.json](reference/london_places.json) contains six static reference locations extracted from the previously audited OpenStreetMap snapshot. It includes ODbL attribution, source, dates, and coordinate limitations. This file is not the NLP training dataset and does not assert current opening hours or booking availability.
