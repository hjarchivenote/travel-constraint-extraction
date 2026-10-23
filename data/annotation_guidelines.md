# Annotation guidelines

**Status: working draft.** The initial rules below reflect the project design discussion. The illustrative record is AI-assisted and pending human review. These guidelines do not yet constitute a frozen annotation or evaluation specification.

## Input and expected output

Model input consists of a short reference itinerary and an English change request. The expected output is a JSON object with a `constraints` array. Each array item represents one requested condition. Do not copy every unchanged itinerary item into the answer.

The reference itinerary supplies context for interpreting the request. Example itineraries are fictional; their times are reference settings, not verified opening hours or booking availability.

## Constraint fields

| Field | Meaning in the current draft |
| --- | --- |
| `type` | Condition category: `place`, `time`, or `walking`. |
| `target` | What the condition applies to, such as `place_visit`, `hotel_return`, `walking_duration`, or `walking_amount`. This vocabulary is still provisional. |
| `operator` | Requested relation or action: `include`, `exclude`, `<=`, `=`, or `minimize` in the cases discussed so far. |
| `value` | Extracted place, time, or numeric limit. Use `null` for a missing required value or when the operation needs no numeric value. |
| `priority` | `hard` for a requirement that must be met; `soft` for a preference. |
| `needs_clarification` | Boolean indicating whether the request and itinerary lack information required to interpret this condition. |
| `unit` | For numeric walking-duration limits, use `minutes`. |
| `scope` | For numeric walking-duration limits: `per_segment` for one continuous walk, `daily_total` for the day's total, or `null` when the required scope is unclear. |

All illustrated conditions use the first six fields. Numeric walking-duration conditions also use `unit` and `scope`. The final machine-readable schema and complete allowed vocabulary will be defined after this draft is reviewed.

## Hard requirements, preferences, and clarification

- Identify the intended meaning from the complete request and itinerary. Cue words alone are not an annotation method.
- An explicit non-negotiable instruction or limit is `hard`. For example, "I must return by 19:00" or "I cannot walk for more than 20 minutes at a time."
- An optional wish is `soft`. For example, "If possible, I would like a cafe break."
- Requirement strength and clarification are separate decisions. A condition can be `hard` and still need clarification.
- Flag clarification when information needed to interpret a condition is absent after checking both the request and itinerary. Preserve the parts that are known rather than inventing the missing information.
- A qualitative preference can be complete without a numeric threshold. "I would prefer less walking" is a `soft` walking-minimization condition with `value: null` and `needs_clarification: false`.
- If requirement strength itself is unclear, hold the example for review. The representation of unresolved strength has not yet been finalized.

## Places

- "Keep the Colosseum visit" means `include`; "Remove the Pantheon visit" means `exclude`.
- Optional inclusion remains `include` but has `priority: soft`.
- For the examples discussed so far, an unqualified explicit instruction to remove a place is `hard`.
- Reuse the reference itinerary's place name when it resolves the mention. A generic category such as "a cafe" can be recorded as `cafe`; do not invent a named business.
- For "that museum," resolve the reference using the itinerary. If more than one candidate remains, keep the requested action, use `value: null`, and flag clarification.

## Times

- Normalize explicit times to local 24-hour `HH:MM` form in the initial same-day examples.
- "By 19:00" uses `operator: <=`; "exactly at 19:00" uses `operator: =`.
- "I must return to the hotel early" preserves the hard hotel-return deadline but uses `value: null` and `needs_clarification: true` if the itinerary does not resolve "early."
- Do not invent a deadline or appointment time.

## Walking

- "At most 20 minutes at a time" uses `value: 20`, `unit: minutes`, `scope: per_segment`, and `operator: <=`.
- "At most 60 minutes in total today" uses `scope: daily_total`.
- "I cannot walk more than 20 minutes" needs clarification if neither the request nor itinerary resolves whether the limit applies per continuous walk or to the whole day. Keep the known limit and use `scope: null`.
- "If possible, reduce walking" uses `target: walking_amount`, `operator: minimize`, `value: null`, and `priority: soft`. No numeric cap or scope is required for this qualitative preference.

## Record envelope and review

The [illustrative record](examples/example_001.json) separates:

- `id`: record identifier.
- `scenario_id`: group identifier used to keep a scenario and its paraphrases in the same split.
- `input`: reference itinerary and change request given to the model.
- `target`: the expected model output.
- `metadata`: authoring, review status, and intended use.

The illustration is excluded from dataset counts and splits. Human review, the final output schema, and matching rules for evaluation are still required before freezing pilot annotations. Never pass `target` or provenance/review metadata to the model as part of its input.
