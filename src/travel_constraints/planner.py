"""Small, explicitly limited demonstration of applying extracted constraints."""

from copy import deepcopy
from math import asin, cos, radians, sin, sqrt

from .weather import select_applicable_constraints


def distance_metres(a, b):
    lat1, lat2 = radians(a["latitude"]), radians(b["latitude"])
    dlat = lat2 - lat1
    dlon = radians(b["longitude"] - a["longitude"])
    return round(6371000 * 2 * asin(sqrt(sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2)))


def apply_constraints(itinerary, extracted, rain, places):
    selected = select_applicable_constraints(extracted, rain)
    plan = deepcopy(itinerary)
    changes, notes = [], []
    active = selected["active"]
    # Preserve an unresolved contradictory place requirement instead of hiding it.
    required_include = {c["value"] for c in active if c["type"] == "place" and c["operator"] == "include" and c["priority"] == "hard"}
    required_exclude = {c["value"] for c in active if c["type"] == "place" and c["operator"] == "exclude" and c["priority"] == "hard"}
    conflicts = required_include & required_exclude
    if conflicts:
        notes.append("Conflicting required visits: " + ", ".join(sorted(conflicts)))
    exact_times = {c["value"] for c in active if c["type"] == "time" and c["operator"] == "=" and c["priority"] == "hard"}
    hard_times = [c for c in active if c["type"] == "time" and c["priority"] == "hard"]
    earliest = max([c["value"] for c in hard_times if c["operator"] == ">="] or ["00:00"])
    latest = min([c["value"] for c in hard_times if c["operator"] == "<="] or ["23:59"])
    time_conflict = len(exact_times) > 1 or earliest > latest or any(not earliest <= value <= latest for value in exact_times)
    if time_conflict:
        notes.append("Conflicting required hotel arrival times; original time retained.")
    for c in sorted(active, key=lambda c: c["priority"] != "hard"):
        if c["type"] == "place" and c["operator"] in {"include", "exclude"}:
            value = c["value"]
            if value in conflicts:
                continue
            if c["operator"] == "exclude" and value not in required_include:
                before = len(plan)
                plan = [stop for stop in plan if stop.get("place") != value]
                if before != len(plan):
                    changes.append(f"Removed {value}.")
            elif c["operator"] == "include" and value not in required_exclude:
                found = [stop for stop in plan if stop.get("place") == value]
                if found:
                    found[0]["annotation"] = "Visit retained"
                    changes.append(f"Kept {value}.")
                else:
                    notes.append(f"Requested visit needs scheduling: {value}.")
        elif c["type"] == "time" and not time_conflict:
            if c["priority"] == "soft" and hard_times:
                continue
            for stop in plan:
                if stop["id"] != "hotel_return":
                    continue
                value = c["value"]
                current = stop["time"]
                if c["operator"] == "=" or (c["operator"] == "<=" and current > value) or (c["operator"] == ">=" and current < value):
                    stop["time"] = value
                changes.append(f"Hotel arrival: {stop['time']} ({c['operator']} {value}).")
        elif c["type"] == "weather":
            for stop in plan:
                if stop["id"] != c["target"]:
                    continue
                if c["operator"] == "replace_with":
                    stop["place"] = "Book cafe (venue to choose)"
                    stop["annotation"] = "Indoor replacement; no business availability asserted"
                    changes.append("Rain alternative: replace the walk with a book cafe visit.")
                elif c["operator"] == "keep":
                    stop["annotation"] = "Outdoor walk retained for this weather scenario"
                    changes.append("Dry alternative: keep the planned walk.")
        elif c["type"] == "place" and c["operator"] == "near":
            by_name = {p["name"]: p for p in places["places"]}
            anchor = by_name.get(c["value"])
            cafe = by_name.get("WatchHouse Somerset House")
            if anchor and cafe and c["value"] == "The Courtauld Gallery":
                for stop in plan:
                    if stop["id"] == "lunch":
                        stop["place"] = cafe["name"]
                        stop["annotation"] = f"Candidate about {distance_metres(anchor, cafe)} m from the gallery in a straight line; opening hours unverified"
                changes.append("Lunch candidate: WatchHouse Somerset House near The Courtauld Gallery.")
            else:
                notes.append(f"Lunch should be near {c['value']}; no verified nearby venue selected.")
        elif c["type"] == "walking":
            if c["operator"] == "minimize":
                notes.append("Less walking is recorded as a preference; route optimization is outside this demo.")
            else:
                notes.append(f"Walking cap recorded: {c['value']} minutes ({c.get('scope')}); route durations are not available to verify it.")
    if selected["pending"]:
        notes.append("Some conditions need clarification or a weather value before they can be applied.")
    hotel = next((s for s in plan if s["id"] == "hotel_return"), None)
    if hotel and any(s["time"] >= hotel["time"] for s in plan if s["id"] != "hotel_return"):
        notes.append("The earlier hotel arrival conflicts with later stops. Scheduling needs review; no feasible route is claimed.")
    return {"itinerary": plan, "changes": list(dict.fromkeys(changes)),
            "notes": list(dict.fromkeys(notes)), "selection": selected,
            "scope": "Illustrative itinerary edits, not a route optimizer or verified travel booking plan."}
