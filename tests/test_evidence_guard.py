import unittest

from travel_constraints.evidence_guard import normalize, priority, time_operator, walking_scope


class EvidenceBoundaryTests(unittest.TestCase):
    def test_arrival_upper_and_lower_bounds_are_not_reversed(self):
        for text in ['Hotel arrival cannot be later than 8:45 pm.',
                     '20:45 is the latest acceptable hotel arrival.',
                     'Getting to the hotel after 20:45 is unacceptable.']:
            with self.subTest(text=text):
                self.assertEqual(time_operator(text), '<=')
        for text in ['Hotel arrival cannot be earlier than 20:45.',
                     '20:45 is the earliest permissible hotel arrival.',
                     'Hotel arrival is not before 20:45.']:
            with self.subTest(text=text):
                self.assertEqual(time_operator(text), '>=')

    def test_a_second_walking_limit_is_not_overwritten_by_the_first(self):
        def limit(number, label):
            return {'type': 'walking', 'target': 'walking_duration', 'operator': '<=',
                    'value': number, 'unit': 'minutes', 'scope': 'per_segment',
                    'priority': label, 'condition': None, 'needs_clarification': False}
        original = {'constraints': [limit(37, 'hard'), limit(11, 'soft')]}
        context = {'change_request': 'Walking segments must not exceed 37 minutes. '
                   'If convenient, limit each segment to 11 minutes.'}
        parsed, _ = normalize(context, original)
        self.assertEqual(parsed, original)
        self.assertEqual(original['constraints'][1]['value'], 11)

    def test_unspecified_walking_scope_requires_confirmation(self):
        item = {'type': 'walking', 'target': 'walking_duration', 'operator': '<=',
                'value': 37, 'unit': 'minutes', 'scope': 'per_segment', 'priority': 'hard',
                'condition': None, 'needs_clarification': False}
        context = {'change_request': 'I have a 37-minute walking cap.'}
        parsed, _ = normalize(context, {'constraints': [item]})
        self.assertIsNone(parsed['constraints'][0]['scope'])
        self.assertTrue(parsed['constraints'][0]['needs_clarification'])
        self.assertEqual(item['scope'], 'per_segment')
        self.assertEqual(normalize(context, parsed)[0], parsed)

    def test_recognized_walking_paraphrases_retain_their_scope(self):
        self.assertEqual(walking_scope('Walk at most 37 minutes at a time.'), 'per_segment')
        self.assertEqual(walking_scope('No walking leg may take more than 37 minutes.'), 'per_segment')
        self.assertEqual(walking_scope('Across the whole outing, allow 37 minutes walking.'), 'daily_total')
        self.assertEqual(walking_scope('All time walking today must stay within 37 minutes.'), 'daily_total')
        self.assertEqual(walking_scope('Each walk today has a 37-minute cap.'), 'per_segment')
        self.assertEqual(walking_scope('Walking segments must stay within 37 minutes.'), 'per_segment')
        self.assertEqual(walking_scope('Walking segments together total at most 37 minutes.'), 'daily_total')

    def test_only_an_explicit_complement_changes_the_walk_weather_condition(self):
        item = {'type': 'weather', 'target': 'outdoor_walk', 'operator': 'keep',
                'value': None, 'priority': 'hard', 'condition': {'weather': 'rain', 'occurs': True},
                'needs_clarification': False}
        request = 'If rain comes, exchange the walk for a book cafe; if not, leave the walk in place.'
        parsed, _ = normalize({'change_request': request}, {'constraints': [item]})
        self.assertFalse(parsed['constraints'][0]['condition']['occurs'])
        self.assertTrue(item['condition']['occurs'])
        unrelated = 'If rain comes, visit a book cafe; if not open, keep the walk in place.'
        parsed, _ = normalize({'change_request': unrelated}, {'constraints': [item]})
        self.assertTrue(parsed['constraints'][0]['condition']['occurs'])

    def test_negated_arrival_is_a_lower_bound(self):
        self.assertEqual(time_operator('Never arrive at the hotel before 18:45.'), '>=')
        self.assertEqual(time_operator('Do not get back to the hotel before 18:45.'), '>=')
        self.assertEqual(time_operator('Get back to the hotel before 18:45.'), '<=')

    def test_an_exact_deadline_is_not_an_exact_arrival(self):
        self.assertEqual(time_operator('Please return early; the exact deadline is undecided.'), '<=')
        self.assertEqual(time_operator('Hotel arrival should be exactly 18:45.'), '=')

    def test_each_walking_leg_including_every(self):
        self.assertEqual(walking_scope('Every walking leg has a maximum of 41 minutes.'), 'per_segment')
        self.assertEqual(walking_scope('Every walk counted together has a maximum of 41 minutes.'), 'daily_total')

    def test_positive_and_negated_requirements(self):
        self.assertEqual(priority('That visit is compulsory.'), 'hard')
        self.assertEqual(priority('That visit is not compulsory.'), 'soft')
        self.assertEqual(priority('Keep the walk if possible.'), 'soft')
        self.assertIsNone(priority('The visit must stay, if possible.'))

    def test_converted_walking_intent_uses_the_limit_priority(self):
        original = {'constraints': [{'type': 'walking', 'target': 'walking_amount',
            'operator': 'minimize', 'value': None, 'priority': 'soft',
            'condition': None, 'needs_clarification': False}]}
        context = {'change_request': 'I can walk at most 41 minutes for the full day.',
                   'reference_itinerary': []}
        parsed, _ = normalize(context, original)
        self.assertEqual(parsed['constraints'][0]['priority'], 'hard')
        self.assertEqual(parsed['constraints'][0]['target'], 'walking_duration')
        context['change_request'] = 'If possible, limit walking to 41 minutes for the full day.'
        parsed, _ = normalize(context, original)
        self.assertEqual(parsed['constraints'][0]['priority'], 'soft')

    def test_weather_priority_is_scoped_to_its_sentence(self):
        item = {'type': 'weather', 'target': 'outdoor_walk', 'operator': 'keep', 'value': None,
                'priority': 'soft', 'condition': {'weather': 'rain', 'occurs': False},
                'needs_clarification': False}
        context = {'change_request': 'Keep the walk in dry weather. Prefer less walking.',
                   'reference_itinerary': []}
        parsed, _ = normalize(context, {'constraints': [item]})
        self.assertEqual(parsed['constraints'][0]['priority'], 'hard')

    def test_a_museum_duration_is_not_a_walking_limit(self):
        item = {'type': 'walking', 'target': 'walking_amount', 'operator': 'minimize',
                'value': None, 'priority': 'soft', 'condition': None, 'needs_clarification': False}
        context = {'change_request': 'Spend 35 minutes in the museum and minimize walking.',
                   'reference_itinerary': []}
        parsed, _ = normalize(context, {'constraints': [item]})
        self.assertEqual(parsed['constraints'], [item])

    def test_dinner_time_does_not_supply_an_unspecified_hotel_time(self):
        item = {'type': 'time', 'target': 'hotel_return', 'operator': '<=', 'value': None,
                'priority': 'hard', 'condition': None, 'needs_clarification': True}
        context = {'change_request': 'Eat dinner at 18:45 and get back to the hotel early.',
                   'reference_itinerary': []}
        parsed, _ = normalize(context, {'constraints': [item]})
        self.assertIsNone(parsed['constraints'][0]['value'])
        self.assertTrue(parsed['constraints'][0]['needs_clarification'])


if __name__ == '__main__':
    unittest.main()
