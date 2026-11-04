import copy
import unittest
from unittest.mock import Mock

from travel_constraints.coverage import complete_extraction, request_groups


def hotel(value='18:30'):
    return {'type': 'time', 'target': 'hotel_return', 'operator': '<=', 'value': value,
            'priority': 'hard', 'needs_clarification': False, 'condition': None}


def result(constraints):
    return {'parsed_output': {'constraints': constraints}, 'raw_output': 'original model text',
            'validation_errors': [], 'model_used': 'primary', 'fallback_used': False, 'attempts': []}


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.context = {'city': 'London', 'reference_itinerary': [],
                        'change_request': 'Keep the walk if dry. Return to the hotel by 18:30.'}

    def test_no_retry_when_explicit_categories_present(self):
        model = Mock()
        self.context['change_request'] = 'Return to the hotel by 18:30.'
        output = complete_extraction(self.context, result([hotel()]), model)
        model.assert_not_called()
        self.assertEqual(output['coverage_unresolved'], [])

    def test_retry_only_missing_text_with_original_reference_and_preserve_raw(self):
        weather = {'type': 'weather', 'target': 'outdoor_walk', 'operator': 'keep', 'value': None,
                   'priority': 'hard', 'needs_clarification': False,
                   'condition': {'weather': 'rain', 'occurs': False}}
        original = result([weather]); snapshot = copy.deepcopy(original)
        model = Mock(return_value=result([hotel()]))
        output = complete_extraction(self.context, original, model)
        model.assert_called_once_with(self.context | {'change_request': 'Return to the hotel by 18:30.'})
        self.assertEqual(output['parsed_output']['constraints'], [weather, hotel()])
        self.assertEqual(output['raw_output'], original['raw_output'])
        self.assertEqual(original, snapshot)

    def test_retry_cannot_replace_an_existing_category_or_add_unrequested_type(self):
        self.context['change_request'] = 'Return to the hotel by 18:30. Put lunch near Example Gallery.'
        unrelated = {'type': 'walking', 'target': 'walking_amount', 'operator': 'minimize',
                     'value': None, 'priority': 'soft', 'condition': None, 'needs_clarification': False}
        model = Mock(return_value=result([hotel('21:00'), unrelated]))
        output = complete_extraction(self.context, result([hotel()]), model)
        self.assertEqual(output['parsed_output']['constraints'], [hotel()])
        self.assertEqual(output['coverage_unresolved'], [('place', 'lunch')])

    def test_invalid_initial_result_stays_invalid(self):
        failed = result([]) | {'parsed_output': None, 'validation_errors': ['invalid']}
        model = Mock()
        self.assertIsNone(complete_extraction(self.context, failed, model)['parsed_output'])
        model.assert_not_called()

    def test_weather_pair_stays_in_same_retry(self):
        self.context['change_request'] = ('Return to the hotel by 18:30. Keep the walk if dry. '
                                         'If it rains, use a book cafe instead.')
        model = Mock(return_value=result([]))
        complete_extraction(self.context, result([hotel()]), model)
        self.assertEqual(model.call_args.args[0]['change_request'],
                         'Keep the walk if dry. If it rains, use a book cafe instead.')

    def test_does_not_repeat_same_full_request(self):
        self.context['change_request'] = 'Return to the hotel by 18:30.'
        model = Mock()
        complete_extraction(self.context, result([]), model)
        model.assert_not_called()

    def test_weather_independent_museum_does_not_require_a_weather_rule(self):
        self.context['change_request'] = "Keep Example Museum regardless of rain."
        self.assertEqual(set(request_groups(self.context)), {('place', 'place_visit')})

    def test_an_activity_duration_does_not_trigger_a_walking_limit_retry(self):
        self.context['change_request'] = 'Spend 35 minutes at the museum and minimize walking.'
        self.assertNotIn(('walking', 'walking_duration'), request_groups(self.context))


if __name__ == '__main__':
    unittest.main()
