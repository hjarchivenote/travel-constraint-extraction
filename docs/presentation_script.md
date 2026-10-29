# Presentation script

Approximate spoken length: 465 words. Rehearse with a timer; target 4:30, maximum 5:00.

## Slide 1

My project extracts travel constraints from English requests. A traveler might ask to keep a gallery visit, return earlier, and choose an indoor activity if it rains. The main task is understanding these instructions and producing structured JSON. I compare a small model before and after LoRA fine-tuning with a larger model using two examples. The itinerary interface makes the extracted conditions visible. It is a demonstration rather than a route optimizer.

## Slide 2

The input includes a reference itinerary, so the model can resolve phrases such as the gallery or the original return time. Each extracted item has a type, target, operator, value, priority, clarification flag, and weather condition. Direct instructions are hard requirements. Prefer indicates a soft preference. Less walking does not imply a numeric limit. If a time or walking scope is missing, the model should preserve that uncertainty instead of inventing an answer.

## Slide 3

The dataset has one hundred reference scenarios and four paraphrases per scenario. Splitting by scenario keeps all four together. Separate wording pools remove identical request text across splits, although the task families and templates still repeat. The labels were AI-reviewed and checked automatically; none are marked human-verified. LoRA trains seven hundred thirty-three thousand parameters in the last four layers. The final CPU run completed three epochs after a GPU stability failure. Test examples were not used for training or prompt selection.

## Slide 4

All three models received the same eighty held-out inputs and output schema. Content F1 requires matching the operator, value, and condition, while priority is scored separately. LoRA achieved F1 0.795, compared with 0.000 for the small baseline and 0.782 for the larger model. It produced 57 fully correct records out of eighty. Strict schema failures count as empty extractions. These scores describe a small synthetic benchmark. The larger model also differs in quantization and prompting, so this does not isolate parameter count.

## Slide 5

The interface displays an actual saved validation prediction, separate from the test set. It can also run the local LoRA model on edited text. Open-Meteo supplies London forecasts. The planner activates the rainy or dry branch, and keeps both pending when forecast coverage is missing. Simulated weather is labeled. Place candidates use attributed OpenStreetMap coordinates. Opening hours, walking routes, and business availability are not verified. The demo shows how structured language output can support a downstream application.

## Slide 6

The main result is a reproducible comparison, not a claim that travel planning is solved. The model still makes important mistakes with walking scope and time relations. The next step would be an independently annotated set of real requests and repeated training seeds. AI assistance was used for code, synthetic labels, experiments, and documentation, and is disclosed in the report. The repository includes the dataset, adapter, raw predictions, evaluation code, and runnable demo so that the result can be inspected.
