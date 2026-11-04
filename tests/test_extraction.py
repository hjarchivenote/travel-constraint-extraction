"""Guard routing against changing valid answers or accepting two invalid outputs."""

import json
import unittest
from unittest.mock import Mock

from travel_constraints.build_data import constraint
from travel_constraints.extraction import extract_with_fallback, repeated_constraint_loop


class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.model_input = {"change_request": "Be at the hotel by 19:00."}
        self.good = json.dumps({"constraints": [constraint("time", "hotel_return", "<=", "19:00")]})

    def test_valid_primary_is_returned_unchanged_without_calling_fallback(self):
        # A wrong but schema-valid value must not trigger an oracle-like correction.
        wrong_value = self.good.replace("19:00", "20:00")
        fallback = Mock(return_value=self.good)
        result = extract_with_fallback(self.model_input, Mock(return_value=wrong_value), fallback)
        self.assertEqual(result["raw_output"], wrong_value)
        self.assertFalse(result["fallback_used"])
        fallback.assert_not_called()

    def test_truncated_json_uses_the_fallback_raw_answer_unchanged(self):
        fallback = Mock(return_value=self.good)
        result = extract_with_fallback(self.model_input, Mock(return_value='{"constraints": ['), fallback)
        self.assertEqual(result["raw_output"], self.good)
        self.assertEqual(result["model_used"], "fallback")
        self.assertEqual(len(result["attempts"]), 2)
        self.assertTrue(result["attempts"][0]["validation_errors"])
        fallback.assert_called_once_with(self.model_input)

    def test_schema_invalid_json_also_triggers_fallback(self):
        invalid = self.good.replace('"hotel_return"', '"place_visit"')
        result = extract_with_fallback(self.model_input, Mock(return_value=invalid), Mock(return_value=self.good))
        self.assertTrue(result["fallback_used"])
        self.assertIsNotNone(result["parsed_output"])

    def test_both_failures_remain_invalid_instead_of_becoming_an_empty_answer(self):
        result = extract_with_fallback(self.model_input, Mock(return_value="not JSON"), Mock(return_value="{}"))
        self.assertIsNone(result["parsed_output"])
        self.assertIsNone(result["model_used"])
        self.assertTrue(result["validation_errors"])
        self.assertEqual(result["raw_output"], "{}")

    def test_model_execution_error_is_not_mislabeled_as_a_schema_failure(self):
        fallback = Mock(return_value=self.good)
        with self.assertRaises(RuntimeError):
            extract_with_fallback(self.model_input, Mock(side_effect=RuntimeError("GPU error")), fallback)
        fallback.assert_not_called()

    def test_generation_loop_is_detected_before_json_is_complete(self):
        item = json.dumps(constraint("weather", "outdoor_walk", "keep", None, rain=False))
        self.assertTrue(repeated_constraint_loop('{"constraints": [' + ','.join([item] * 3)))
        self.assertFalse(repeated_constraint_loop('{"constraints": [' + ','.join([item] * 2)))

    def test_distinct_conditions_and_braces_inside_place_names_are_not_a_loop(self):
        items = [constraint("place", "place_visit", "include", 'Gallery "A}B"'),
                 constraint("weather", "outdoor_walk", "keep", None, rain=False),
                 constraint("weather", "outdoor_walk", "replace_with", "book_cafe", rain=True)]
        self.assertFalse(repeated_constraint_loop(json.dumps({"constraints": items})))

    def test_even_complete_json_with_a_generation_loop_uses_fallback(self):
        repeated = json.dumps({"constraints": [json.loads(self.good)["constraints"][0]] * 3})
        result = extract_with_fallback(self.model_input, Mock(return_value=repeated), Mock(return_value=self.good))
        self.assertTrue(result["fallback_used"])
        self.assertEqual(result["raw_output"], self.good)


if __name__ == "__main__":
    unittest.main()
