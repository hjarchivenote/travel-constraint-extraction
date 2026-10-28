"""Check this controlled corpus independently of its generator.

These checks support AI review; passing is not human annotation approval.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

from .contract import validate_output


def audit_records(records):
    issues = []
    groups, requests, identities = defaultdict(set), defaultdict(set), defaultdict(set)
    ids = set()
    expected_counts = {"weather_alternative": 2, "combined": 6}
    for row in records:
        record_id = row["id"]
        def check(ok, message):
            if not ok:
                issues.append({"id": record_id, "issue": message})
        check(record_id not in ids, "Duplicate record ID")
        ids.add(record_id)
        check(not validate_output(row["target"]), "Invalid annotation schema")
        check(row["input"]["city"] == "London", "Unexpected city")
        groups[row["scenario_id"]].add(row["split"])
        text = " ".join(row["input"]["change_request"].casefold().split())
        requests[text].add(row["split"])
        items = row["target"]["constraints"]
        family = row["family"]
        check(len(items) == expected_counts.get(family, 1), "Wrong number of annotated conditions")
        itinerary = {item["id"]: item for item in row["input"]["reference_itinerary"]}
        if family == "place_include":
            identities[items[0]["value"]].add(items[0]["priority"])
        for item in items:
            if item["type"] == "place":
                anchor = itinerary["gallery_visit"]["place"] if item["target"] == "lunch" or family == "place_include" else itinerary["museum_visit"]["place"]
                check(item["value"] == anchor, "Place value does not match its reference stop")
            if item["type"] == "walking" and item["target"] == "walking_amount":
                check(item["value"] is None and item["priority"] == "soft", "Qualitative walking wish has an invented limit or wrong strength")
            if item["type"] == "walking" and item["target"] == "walking_duration":
                numbers = {int(v) for v in re.findall(r"(\d+)(?:-minute|\s+(?:walking\s+)?minutes?)", text)}
                check(numbers == {item["value"]}, "Walking value disagrees with the request")
                if family == "ambiguous_walking_scope":
                    check(item["scope"] is None and item["needs_clarification"], "Unstated walking scope was invented")
                else:
                    daily = bool(re.search(r"total|combined|daily|entire day|sum of|day's|whole day|added together|all the walks", text))
                    check(item["scope"] == ("daily_total" if daily else "per_segment"), "Walking scope disagrees with wording")
                    check(not item["needs_clarification"], "Explicit walking scope incorrectly marked unresolved")
            if item["type"] == "time":
                if family == "ambiguous_time":
                    check(item["value"] is None and item["needs_clarification"], "An unspecified deadline was invented")
                elif family == "combined":
                    check(item["value"] == itinerary["hotel_return"]["time"] and item["operator"] == "=", "Original hotel arrival not preserved exactly")
                else:
                    times = set()
                    for hour, minute, period in re.findall(r"\b(\d{1,2}):(\d{2})(?:\s*(am|pm))?\b", text):
                        hour = int(hour)
                        if period:
                            hour = hour % 12 + (12 if period == "pm" else 0)
                        times.add(f"{hour:02d}:{minute}")
                    check(times == {item["value"]}, "Hotel clock value disagrees with request")
                    exact = bool(re.search(r"exact|precis|on the dot|fixed|not earlier or later|neither before|no earlier or later|lock", text))
                    check(item["operator"] == ("=" if exact else "<="), "Hotel equality/deadline operator disagrees with wording")
        if family in {"weather_alternative", "combined"}:
            branches = {(item["operator"], item["value"], item["condition"]["occurs"])
                        for item in items if item["type"] == "weather" and item["condition"]}
            check(branches == {("keep", None, False), ("replace_with", "book_cafe", True)}, "Rain and dry alternatives are incomplete or reversed")
    if any(len(splits) > 1 for splits in groups.values()):
        issues.append({"issue": "Reference scenario crosses splits"})
    leaks = sum(len(splits) > 1 for splits in requests.values())
    if leaks:
        issues.append({"issue": "Identical request text crosses splits", "groups": leaks})
    if any(strengths != {"hard", "soft"} for strengths in identities.values()):
        issues.append({"issue": "Place identity predicts requirement strength"})
    split_counts = dict(Counter(row["split"] for row in records))
    if len(records) != 400 or len(groups) != 100 or split_counts != {"train": 280, "validation": 40, "test": 80}:
        issues.append({"issue": "Corpus size or split counts changed"})
    return {"records": len(records), "scenario_groups": len(groups),
            "split_counts": split_counts,
            "unique_request_texts": len(requests), "cross_split_identical_requests": leaks,
            "human_reviewed_records": sum(row["metadata"].get("human_reviewed", False) for row in records),
            "unique_model_inputs": len({json.dumps(row["input"], sort_keys=True) for row in records}),
            "issues": issues, "passed": not issues,
            "limits": "Consistency checks and AI review do not establish human agreement or real-user generalization."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = Path(args.records)
    records = [json.loads(line) for line in source.read_text().splitlines() if line.strip()]
    result = audit_records(records)
    result["dataset_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
