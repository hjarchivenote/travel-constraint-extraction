"""The output contract shared by prompts, validation, and evaluation."""

import json
from pathlib import Path

from jsonschema import Draft202012Validator

SCHEMA_PATH = Path(__file__).with_name("output_schema.json")
SCHEMA = json.loads(SCHEMA_PATH.read_text())
Draft202012Validator.check_schema(SCHEMA)
VALIDATOR = Draft202012Validator(SCHEMA)

SYSTEM_PROMPT = """Extract requested changes to a one-day London itinerary.
Return ONLY a JSON object {"constraints": [...]}; no markdown or explanation.
Each constraint has: type, target, operator, value, priority, needs_clarification, condition.
type is place, time, walking, or weather. priority is hard (required), soft (optional), or null if unclear.
condition is null unless conditional: {"weather":"rain","occurs":true} or false for no rain.
For place inclusion/exclusion: target="place_visit", operator="include"/"exclude", value=canonical place name or requested category.
For a nearby lunch: type="place", target="lunch", operator="near", value=the named anchor place. Do not invent a distance.
For hotel return: type="time", target="hotel_return", value="HH:MM"; operator="<=" means by, "=" means exactly at, ">=" means not before.
For walking limits: type="walking", target="walking_duration", operator="<=", numeric value, unit="minutes", scope="per_segment" or "daily_total".
If walking scope is missing, scope=null and needs_clarification=true. Never invent a limit.
For less walking: type="walking", target="walking_amount", operator="minimize", value=null, priority="soft", needs_clarification=false.
For conditional activities: type="weather", target=itinerary activity id, operator="keep", value=null; or operator="replace_with", value=replacement category such as "book_cafe". Attach the rain condition.
For avoiding outdoor activities in rain: type="weather", target="outdoor_activity", operator="avoid", value=null with the rain condition.
Resolve 'the gallery', 'the walk', and 'the original return time' from the reference itinerary.
Missing required time/place values are null with needs_clarification=true. An ordinary clear condition has needs_clarification=false.
Unqualified direct instructions are hard; 'if possible', 'prefer', and similar optional wishes are soft.
Extract ALL requested conditions, including both weather alternatives. Keep hard and soft conditions even when they conflict.
Do not copy unchanged itinerary facts into the output unless the request explicitly asks to keep them.
"""


def validate_output(value):
    return [error.message for error in VALIDATOR.iter_errors(value)]


def parse_output(text):
    """Strict JSON parsing: fenced prose does not count as valid JSON output."""
    try:
        value = json.loads(text)
    except (json.JSONDecodeError, TypeError) as error:
        return None, [str(error)]
    errors = validate_output(value)
    return (None if errors else value), errors


def messages_for(record, demonstrations=()):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for example in demonstrations:
        messages.extend([
            {"role": "user", "content": json.dumps(example["input"], ensure_ascii=False)},
            {"role": "assistant", "content": json.dumps(example["target"], ensure_ascii=False)},
        ])
    messages.append({"role": "user", "content": json.dumps(record["input"], ensure_ascii=False)})
    return messages
