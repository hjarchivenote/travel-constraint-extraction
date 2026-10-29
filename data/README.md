# Dataset

`travel_requests.jsonl` is the frozen v2 NLP corpus: **400 synthetic records, 100 reference scenarios × four request paraphrases**. `splits.json` records the 280 training, 40 validation, and 80 test IDs. All paraphrases of a scenario stay together. There are 400 unique full inputs and 252 distinct request texts; no exact request text crosses splits. Shared semantic frames and within-split wording remain.

**Annotations are AI-reviewed, not human-verified.** The review covered wording patterns and instantiated values, with automated consistency checks on all records. No human approval is inferred. `metadata.json` and `ai_review_v2.json` record this distinction. Treat scores as a controlled synthetic experiment rather than a real-user benchmark.

The v2 review removed 37 cross-split duplicate-request groups present in v1 and removed an association between gallery identity and hard/soft labels. These changes preceded v2 model experiments. The frozen dataset SHA-256 is:

```text
19466ef251eaa6fa81db7014e5ee9e180e95c71deb2b103e2b06f4df6e231aa5
```

The schema and labeling instructions are executable in `src/travel_constraints/output_schema.json` and `contract.py`. Targets must not be altered after seeing held-out predictions to improve a reported score. Any future annotation corrections require a new version and a clearly separated experiment.

## Supporting London sources

`reference/london_places.json` contains six static OpenStreetMap locations with ODbL attribution and snapshot metadata. Coordinates may be feature centroids, not entrances; opening hours and availability are not verified.

`reference/london_forecast.json` is a timestamped Open-Meteo / ECMWF forecast snapshot, under CC BY 4.0. It supports the demonstration, not the training targets. The interface labels forecasts, simulations, and unknown coverage separately. See `THIRD_PARTY_NOTICES.md` for sources and terms.

Original project materials have no additional blanket reuse license; see `LICENSE_SCOPE.md`. Third-party rights and terms remain in force.
