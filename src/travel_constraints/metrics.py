"""One-to-one constraint matching, independent of JSON/list ordering."""

import argparse
from collections import defaultdict
import json
from pathlib import Path
import unicodedata

from .contract import parse_output

CONTENT_FIELDS = ("type", "target", "operator", "value", "unit", "scope", "condition")


def normalized(value):
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        return " ".join(unicodedata.normalize("NFKC", value).casefold().split())
    if isinstance(value, dict):
        return {key: normalized(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return [normalized(item) for item in value]
    return value


def content_key(constraint):
    return json.dumps(normalized({key: constraint.get(key) for key in CONTENT_FIELDS}), sort_keys=True)


def score_one(gold, prediction):
    expected = gold["constraints"]
    actual = prediction["constraints"] if prediction is not None else []
    expected_groups, actual_groups = defaultdict(list), defaultdict(list)
    for item in expected:
        expected_groups[content_key(item)].append(item)
    for item in actual:
        actual_groups[content_key(item)].append(item)
    matched = priority_correct = priority_total = clarification_correct = 0
    for key, gold_items in expected_groups.items():
        predicted_items = actual_groups.get(key, [])
        # Pair identical labels first when a duplicate content constraint occurs.
        remaining = list(predicted_items)
        for item in gold_items:
            if not remaining:
                continue
            same = max(range(len(remaining)), key=lambda i: (
                remaining[i].get("priority") == item.get("priority"),
                remaining[i].get("needs_clarification") == item.get("needs_clarification"),
            ))
            other = remaining.pop(same)
            matched += 1
            if item.get("priority") in {"hard", "soft"}:
                priority_total += 1
                priority_correct += other.get("priority") == item.get("priority")
            clarification_correct += other.get("needs_clarification") == item.get("needs_clarification")
    full_key = lambda item: json.dumps(normalized({
        **{key: item.get(key) for key in CONTENT_FIELDS},
        "priority": item.get("priority"), "needs_clarification": item.get("needs_clarification"),
    }), sort_keys=True)
    return {
        "tp": matched, "fp": len(actual) - matched, "fn": len(expected) - matched,
        "priority_correct": priority_correct, "priority_total": priority_total,
        "clarification_correct": clarification_correct,
        "exact": prediction is not None and sorted(map(full_key, expected)) == sorted(map(full_key, actual)),
    }


def summarize(records, predictions):
    if not records:
        raise ValueError("Cannot evaluate an empty reference set.")
    by_id = {}
    for prediction in predictions:
        if prediction["id"] in by_id:
            raise ValueError("Duplicate prediction ID")
        by_id[prediction["id"]] = prediction
    if set(by_id) != {record["id"] for record in records}:
        raise ValueError("Prediction IDs must match the selected reference records exactly.")
    totals = defaultdict(int)
    valid = exact = 0
    seconds = []
    for record in records:
        result = by_id[record["id"]]
        prediction = parse_output(result["raw_output"])[0] if "raw_output" in result else result["parsed_output"]
        valid += prediction is not None
        score = score_one(record["target"], prediction)
        exact += score["exact"]
        for key in ("tp", "fp", "fn", "priority_correct", "priority_total", "clarification_correct"):
            totals[key] += score[key]
        seconds.append(result["inference_seconds"])
    precision = totals["tp"] / (totals["tp"] + totals["fp"]) if totals["tp"] + totals["fp"] else 0.0
    recall = totals["tp"] / (totals["tp"] + totals["fn"]) if totals["tp"] + totals["fn"] else 0.0
    return {
        "records": len(records), "precision": precision, "recall": recall,
        "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "priority_accuracy_on_matched": totals["priority_correct"] / totals["priority_total"] if totals["priority_total"] else None,
        "clarification_accuracy_on_matched": totals["clarification_correct"] / totals["tp"] if totals["tp"] else None,
        "schema_validity_rate": valid / len(records), "exact_record_accuracy": exact / len(records),
        "mean_inference_seconds_including_first_request": sum(seconds) / len(seconds),
        "counts": dict(totals),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", required=True)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--output", required=True)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--ids", help="Expected record IDs, including any missing predictions")
    selection.add_argument("--split", choices=["train", "validation", "test"])
    args = parser.parse_args()
    predictions = [json.loads(line) for line in Path(args.predictions).read_text().splitlines() if line.strip()]
    records = [json.loads(line) for line in Path(args.records).read_text().splitlines() if line.strip()]
    if args.ids:
        ids = set(json.loads(Path(args.ids).read_text()))
        records = [record for record in records if record["id"] in ids]
        if {record["id"] for record in records} != ids:
            raise SystemExit("Some expected reference IDs do not exist.")
    else:
        records = [record for record in records if record["split"] == args.split]
    summary = summarize(records, predictions)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
