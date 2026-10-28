"""Protect evaluation against order, label, duplicate, and condition errors."""

import unittest

from travel_constraints.build_data import build_records, constraint
from travel_constraints.contract import parse_output, validate_output
from travel_constraints.metrics import score_one, summarize
from travel_constraints.weather import rain_in_window, select_applicable_constraints


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.deadline = constraint("time", "hotel_return", "<=", "19:00")
        self.place = constraint("place", "place_visit", "include", "Tate Modern")

    def test_condition_order_is_irrelevant(self):
        score = score_one({"constraints": [self.deadline, self.place]},
                          {"constraints": [self.place, self.deadline]})
        self.assertTrue(score["exact"])
        self.assertEqual((score["tp"], score["fp"], score["fn"]), (2, 0, 0))

    def test_priority_error_does_not_hide_correct_extraction(self):
        wrong = self.deadline | {"priority": "soft"}
        score = score_one({"constraints": [self.deadline]}, {"constraints": [wrong]})
        self.assertEqual(score["tp"], 1)
        self.assertEqual(score["priority_correct"], 0)
        self.assertFalse(score["exact"])

    def test_wrong_time_is_false_positive_and_false_negative(self):
        wrong = self.deadline | {"value": "20:00"}
        score = score_one({"constraints": [self.deadline]}, {"constraints": [wrong]})
        self.assertEqual((score["tp"], score["fp"], score["fn"]), (0, 1, 1))

    def test_weather_condition_cannot_be_discarded(self):
        rainy = constraint("weather", "outdoor_walk", "keep", None, rain=True)
        dry = constraint("weather", "outdoor_walk", "keep", None, rain=False)
        score = score_one({"constraints": [rainy]}, {"constraints": [dry]})
        self.assertEqual((score["tp"], score["fp"], score["fn"]), (0, 1, 1))

    def test_duplicate_prediction_does_not_match_twice(self):
        score = score_one({"constraints": [self.place]}, {"constraints": [self.place, self.place]})
        self.assertEqual((score["tp"], score["fp"], score["fn"]), (1, 1, 0))

    def test_duplicate_label_matching_is_order_invariant(self):
        gold = [self.place, self.place | {"priority": "soft", "needs_clarification": True}]
        predicted = [self.place | {"needs_clarification": True}, self.place | {"priority": "soft"}]
        left = score_one({"constraints": gold}, {"constraints": predicted})
        right = score_one({"constraints": gold}, {"constraints": list(reversed(predicted))})
        self.assertEqual(left, right)
        self.assertEqual(left["priority_correct"], 2)

    def test_invalid_output_is_not_repaired_into_a_correct_answer(self):
        parsed, errors = parse_output('```json\n{"constraints": []}\n```')
        self.assertIsNone(parsed)
        self.assertTrue(errors)
        self.assertEqual(score_one({"constraints": [self.place]}, None)["fn"], 1)

    def test_impossible_clock_is_rejected(self):
        self.assertTrue(validate_output({"constraints": [self.deadline | {"value": "29:00"}]}))

    def test_place_name_cannot_replace_the_target_field(self):
        wrong = self.place | {"target": "Tate Modern", "value": None, "needs_clarification": True}
        self.assertTrue(validate_output({"constraints": [wrong]}))

    def test_conditional_replacement_requires_a_destination(self):
        wrong = constraint("weather", "outdoor_walk", "replace_with", None, rain=True)
        self.assertTrue(validate_output({"constraints": [wrong]}))

    def test_incomplete_predictions_cannot_silently_improve_scores(self):
        records = [{"id": "a", "target": {"constraints": [self.place]}},
                   {"id": "b", "target": {"constraints": [self.deadline]}}]
        predictions = [{"id": "a", "parsed_output": {"constraints": [self.place]}, "inference_seconds": 1.0}]
        with self.assertRaises(ValueError):
            summarize(records, predictions)

    def test_numeric_formatting_does_not_change_a_walking_limit(self):
        whole = constraint("walking", "walking_duration", "<=", 15, unit="minutes", scope="per_segment")
        score = score_one({"constraints": [whole]}, {"constraints": [whole | {"value": 15.0}]})
        self.assertTrue(score["exact"])

    def test_400_candidates_preserve_scenario_groups(self):
        records = build_records()
        self.assertEqual(len(records), 400)
        groups = {}
        for record in records:
            groups.setdefault(record["scenario_id"], set()).add(record["split"])
        self.assertEqual(len(groups), 100)
        self.assertTrue(all(len(splits) == 1 for splits in groups.values()))
        self.assertTrue(all(record["metadata"]["human_reviewed"] is False for record in records))


class WeatherTests(unittest.TestCase):
    def snapshot(self, rain, showers):
        return {"retrieved_at": "2026-10-28T12:00:00Z", "data": {"hourly": {
            "time": ["2026-10-29T14:00", "2026-10-29T15:00"], "rain": rain, "showers": showers}}}

    def test_walk_at_14_uses_bucket_ending_at_15(self):
        context = rain_in_window(self.snapshot([10.0, 0.0], [0.0, 0.0]),
                                 "2026-10-29T14:00", "2026-10-29T15:00")
        self.assertIs(context["rain"], False)
        self.assertEqual(context["bucket_ends_local"], ["2026-10-29T15:00"])

    def test_missing_rain_is_not_assumed_dry(self):
        context = rain_in_window(self.snapshot([0.0, None], [0.0, 0.0]),
                                 "2026-10-29T14:00", "2026-10-29T15:00")
        self.assertIsNone(context["rain"])

    def test_weather_selects_only_one_alternative(self):
        items = {"constraints": [constraint("weather", "outdoor_walk", "keep", None, rain=False),
                                  constraint("weather", "outdoor_walk", "replace_with", "book_cafe", rain=True),
                                  constraint("place", "place_visit", "include", "Tate Modern")]}
        result = select_applicable_constraints(items, rain=True)
        self.assertEqual(len(result["active"]), 2)
        self.assertEqual(result["active"][0]["operator"], "replace_with")
        self.assertEqual(len(result["inactive"]), 1)


if __name__ == "__main__":
    unittest.main()
