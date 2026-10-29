import json
from pathlib import Path
import unittest

from travel_constraints.build_data import constraint
from travel_constraints.planner import apply_constraints


class PlannerTests(unittest.TestCase):
    def setUp(self):
        self.plan = [{"id": "gallery_visit", "place": "The Courtauld Gallery", "time": "10:00"},
                     {"id": "lunch", "time": "12:30"},
                     {"id": "outdoor_walk", "place": "South Bank", "time": "14:00"},
                     {"id": "museum_visit", "place": "Tate Modern", "time": "16:00"},
                     {"id": "hotel_return", "time": "20:00"}]
        self.places = json.loads(Path("data/reference/london_places.json").read_text())

    def apply(self, items, rain=False):
        return apply_constraints(self.plan, {"constraints": items}, rain, self.places)

    def test_rain_replaces_only_the_walk(self):
        r = self.apply([constraint("weather", "outdoor_walk", "replace_with", "book_cafe", rain=True),
                        constraint("place", "place_visit", "include", "Tate Modern")], rain=True)
        self.assertIn("Book cafe", r["itinerary"][2]["place"])
        self.assertEqual(r["itinerary"][3]["place"], "Tate Modern")
        self.assertEqual(self.plan[2]["place"], "South Bank")

    def test_unresolved_deadline_is_not_invented(self):
        r = self.apply([constraint("time", "hotel_return", "<=", None, clarify=True)])
        self.assertEqual(r["itinerary"][-1]["time"], "20:00")
        self.assertEqual(len(r["selection"]["pending"]), 1)

    def test_hard_deadline_beats_optional_arrival(self):
        r = self.apply([constraint("time", "hotel_return", "<=", "19:00"),
                        constraint("time", "hotel_return", "=", "21:00", priority="soft")])
        self.assertEqual(r["itinerary"][-1]["time"], "19:00")

    def test_contradictory_required_times_are_reported(self):
        r = self.apply([constraint("time", "hotel_return", "<=", "18:00"),
                        constraint("time", "hotel_return", ">=", "19:00")])
        self.assertEqual(r["itinerary"][-1]["time"], "20:00")
        self.assertTrue(any("Conflicting" in note for note in r["notes"]))

    def test_unknown_weather_preserves_both_pending_alternatives(self):
        r = self.apply([constraint("weather", "outdoor_walk", "keep", None, rain=False),
                        constraint("weather", "outdoor_walk", "replace_with", "book_cafe", rain=True)], rain=None)
        self.assertEqual(r["itinerary"][2]["place"], "South Bank")
        self.assertEqual(len(r["selection"]["pending"]), 2)

    def test_lunch_candidate_is_explicitly_a_reference(self):
        r = self.apply([constraint("place", "lunch", "near", "The Courtauld Gallery")])
        self.assertEqual(r["itinerary"][1]["place"], "WatchHouse Somerset House")
        self.assertIn("unverified", r["itinerary"][1]["annotation"])


if __name__ == "__main__":
    unittest.main()
