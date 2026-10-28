"""Build 400 controlled synthetic candidates with scenario-disjoint splits.

Targets are constructed from the same explicit semantic frames as the text.
This does not replace human annotation review or establish real-user accuracy.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random

from .contract import messages_for, validate_output


def constraint(kind, target, operator, value, *, priority="hard", clarify=False, rain=None, **extra):
    return {"type": kind, "target": target, "operator": operator, "value": value,
            "priority": priority, "needs_clarification": clarify,
            "condition": None if rain is None else {"weather": "rain", "occurs": rain}, **extra}


def clock(minutes):
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def readable_time(value):
    hour, minute = map(int, value.split(":"))
    return f"{hour % 12 or 12}:{minute:02d} {'pm' if hour >= 12 else 'am'}"


def scenario(family, index):
    gallery = "National Gallery" if index % 2 == 0 else "The Courtauld Gallery"
    museum = "Tate Modern" if index % 3 else "Sir John Soane's Museum"
    hotel_time = clock(20 * 60 + index * 10)
    itinerary = [
        {"id": "gallery_visit", "place": gallery, "time": clock(10 * 60 + index * 5)},
        {"id": "lunch", "time": "12:30"},
        {"id": "outdoor_walk", "place": "South Bank", "time": "14:00"},
        {"id": "museum_visit", "place": museum, "time": "16:00"},
        {"id": "hotel_return", "time": hotel_time},
    ]
    if family == "place_include":
        soft = index % 2 == 1
        priority = "soft" if soft else "hard"
        if soft:
            texts = [f"If possible, keep the visit to {gallery}.", f"I would prefer to retain {gallery} on the itinerary.",
                     f"I'd like to visit {gallery} if there is room for it.", f"Please include {gallery} when feasible."]
        else:
            texts = [f"You must keep the visit to {gallery}.", f"Do not remove {gallery}; that visit is essential.",
                     f"Make sure {gallery} stays in my plan.", f"Visiting {gallery} is a requirement."]
        gold = [constraint("place", "place_visit", "include", gallery, priority=priority)]
    elif family == "place_exclude":
        texts = [f"Remove {museum} from the itinerary.", f"I do not want to visit {museum}. Leave it out.",
                 f"Please take the {museum} visit out of my day.", f"Skip {museum} entirely."]
        gold = [constraint("place", "place_visit", "exclude", museum)]
    elif family == "hotel_time":
        value = clock(18 * 60 + index * 15)
        spoken = readable_time(value)
        if index % 2 == 0:
            texts = [f"I must return to the hotel by {spoken}.", f"Make sure I reach my hotel no later than {value}.",
                     f"My hotel return deadline is {spoken}.", f"Getting back to the hotel by {value} is mandatory."]
            operator = "<="
        else:
            texts = [f"I need to be back at the hotel exactly at {spoken}.", f"Set my hotel return to precisely {value}.",
                     f"The hotel arrival must be at {spoken}, not earlier or later.", f"Use {value} as my fixed hotel return time."]
            operator = "="
        gold = [constraint("time", "hotel_return", operator, value)]
    elif family == "walking_limit":
        daily = index % 2 == 1
        value = 40 + index * 5 if daily else 10 + index * 5
        if daily:
            texts = [f"I cannot walk for more than {value} minutes in total today.", f"Limit my total walking for the day to {value} minutes.",
                     f"All walks combined must take at most {value} minutes.", f"My daily walking allowance is no more than {value} minutes."]
        else:
            texts = [f"I cannot walk for more than {value} minutes at a time.", f"Each continuous walk must last at most {value} minutes.",
                     f"Keep every uninterrupted walking stretch to {value} minutes or less.", f"I need a break after at most {value} minutes of continuous walking."]
        gold = [constraint("walking", "walking_duration", "<=", value, unit="minutes",
                           scope="daily_total" if daily else "per_segment")]
    elif family == "walking_minimize":
        texts = ["I would prefer less walking throughout the itinerary.", "Please keep the amount of walking as low as possible.",
                 "Try to reduce walking across the whole day where possible.", "Of the available options, I would prefer the one with less walking."]
        gold = [constraint("walking", "walking_amount", "minimize", None, priority="soft")]
    elif family == "ambiguous_time":
        texts = ["I must be back at the hotel early this evening.", "Make my hotel return early tonight; that is essential.",
                 "I need an early hotel return today.", "Returning to the hotel early is a requirement for me."]
        gold = [constraint("time", "hotel_return", "<=", None, clarify=True)]
    elif family == "ambiguous_walking_scope":
        value = 15 + index * 5
        texts = [f"I cannot walk for more than {value} minutes.", f"My walking limit is {value} minutes.",
                 f"Do not let my walking exceed {value} minutes.", f"I can manage at most {value} minutes of walking."]
        gold = [constraint("walking", "walking_duration", "<=", value, clarify=True, unit="minutes", scope=None)]
    elif family == "near_lunch":
        texts = [f"Have lunch near {gallery}.", f"Place my lunch stop close to {gallery}.",
                 f"Find somewhere to eat lunch in the vicinity of {gallery}.", f"Arrange lunch nearby the gallery, {gallery}."]
        gold = [constraint("place", "lunch", "near", gallery)]
    elif family in {"weather_alternative", "combined"}:
        gold = [constraint("weather", "outdoor_walk", "keep", None, rain=False),
                constraint("weather", "outdoor_walk", "replace_with", "book_cafe", rain=True)]
        if family == "weather_alternative":
            texts = ["Keep the South Bank walk if it does not rain. If it rains, replace the walk with a book cafe visit.",
                     "When it is raining, go to a bookshop cafe instead of the planned walk; otherwise keep the walk.",
                     "No rain means I will do the scheduled walk. Rain means a book cafe must replace it.",
                     "Retain the outdoor walk in dry weather, but substitute a book cafe for it when it rains."]
        else:
            gold = [constraint("place", "lunch", "near", gallery), *gold,
                    constraint("place", "place_visit", "include", museum),
                    constraint("time", "hotel_return", "=", hotel_time),
                    constraint("walking", "walking_amount", "minimize", None, priority="soft")]
            texts = [
                f"Have lunch near {gallery}. If it does not rain, keep the walk; if it rains, replace it with a book cafe. Keep {museum} whatever the weather. Return to the hotel at the original time. Minimize walking throughout.",
                f"I want lunch close to the gallery. Keep the walk when there is no rain and use a bookshop cafe instead when it rains. {museum} must stay regardless of the forecast. The hotel return must remain at {hotel_time}. Please reduce walking as much as possible.",
                f"Lunch should be near {gallery}. The weather decides the walk: no rain, keep it; rain, replace it with a book cafe. Do not drop {museum} because of weather. I must reach the hotel exactly at {readable_time(hotel_time)}. I would prefer less walking overall.",
                f"Arrange lunch in the vicinity of the gallery and keep {museum} in all weather. Keep the South Bank walk if it is not raining, otherwise substitute a book cafe. Preserve the original hotel arrival time exactly, and keep walking to a minimum.",
            ]
    else:
        raise ValueError(f"Unknown family: {family}")
    return itinerary, texts, {"constraints": gold}


def build_records(seed=42):
    families = ["place_include", "place_exclude", "hotel_time", "walking_limit", "walking_minimize",
                "ambiguous_time", "ambiguous_walking_scope", "near_lunch", "weather_alternative", "combined"]
    rng = random.Random(seed)
    records = []
    seen_scenarios = set()
    for family in families:
        order = list(range(10))
        rng.shuffle(order)
        splits = {index: "train" if position < 7 else "validation" if position == 7 else "test"
                  for position, index in enumerate(order)}
        for index in range(10):
            itinerary, texts, target = scenario(family, index)
            errors = validate_output(target)
            if errors:
                raise ValueError(f"Invalid constructed target: {family}/{index}: {errors}")
            fingerprint = hashlib.sha256(json.dumps([itinerary, target], sort_keys=True).encode()).hexdigest()
            if fingerprint in seen_scenarios:
                raise ValueError("Duplicate semantic scenario; do not split it under different IDs.")
            seen_scenarios.add(fingerprint)
            for variant, text in enumerate(texts):
                scenario_id = f"{family}_{index:02d}"
                records.append({
                    "id": f"{scenario_id}_{variant}", "scenario_id": scenario_id,
                    "family": family, "split": splits[index],
                    "input": {"city": "London", "reference_itinerary": itinerary, "change_request": text},
                    "target": target,
                    "metadata": {"authoring": "AI-assisted controlled template generation",
                                 "human_reviewed": False, "scenario_fingerprint": fingerprint,
                                 "itinerary_times": "fictional reference settings, not opening hours or bookings"},
                })
    if len(records) != 400 or len(seen_scenarios) != 100:
        raise ValueError("Dataset must contain 400 candidates in 100 scenario groups.")
    return records


def export_training(records, directory, train_limit=20, valid_limit=4):
    directory.mkdir(parents=True, exist_ok=True)
    # Development run deliberately exports no final test data.
    for split, name, limit in [("train", "train.jsonl", train_limit), ("validation", "valid.jsonl", valid_limit)]:
        selected = [record for record in records if record["split"] == split]
        # Interleave scenario families rather than taking only the first family.
        buckets = {}
        for record in selected:
            buckets.setdefault(record["family"], []).append(record)
        interleaved = []
        while any(buckets.values()):
            for bucket in buckets.values():
                if bucket:
                    interleaved.append(bucket.pop(0))
        selected = interleaved[:limit]
        with (directory / name).open("w") as handle:
            for record in selected:
                messages = messages_for(record) + [{"role": "assistant", "content": json.dumps(record["target"])}]
                handle.write(json.dumps({"messages": messages}) + "\n")
        (directory / f"{split}_ids.json").write_text(json.dumps([record["id"] for record in selected], indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="outputs/corpus")
    parser.add_argument("--train-limit", type=int, default=20)
    parser.add_argument("--valid-limit", type=int, default=4)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    output = Path(args.output)
    if (output / "records.jsonl").exists() and not args.overwrite:
        raise SystemExit("Corpus already exists. Choose a new output directory or explicitly use --overwrite.")
    output.mkdir(parents=True, exist_ok=True)
    records = build_records()
    (output / "records.jsonl").write_text("".join(json.dumps(record) + "\n" for record in records))
    metadata = {"records": len(records), "scenario_groups": 100, "split_records": dict(Counter(record["split"] for record in records)),
                "seed": 42, "human_reviewed_records": 0, "status": "candidates_pending_human_review",
                "generation_method": "semantic frames rendered with four authored paraphrase templates per family",
                "limitation": "Controlled synthetic language; shared template families across splits. Not an independent real-user benchmark.",
                "test_policy": "Test candidates are reserved for human review and must not be used for training or prompt selection."}
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    export_training(records, output / "pilot_training", args.train_limit, args.valid_limit)
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
