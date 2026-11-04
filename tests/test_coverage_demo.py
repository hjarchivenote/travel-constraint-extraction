import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch


class CoverageDemoTests(unittest.TestCase):
    def test_enabled_demo_completes_missing_field_and_retains_generation_provenance(self):
        path = Path(__file__).resolve().parents[1] / 'demo/app.py'
        spec = importlib.util.spec_from_file_location('coverage_demo_test', path)
        app = importlib.util.module_from_spec(spec); spec.loader.exec_module(app)
        weather = {'type': 'weather', 'target': 'outdoor_walk', 'operator': 'keep', 'value': None,
                   'priority': 'hard', 'needs_clarification': False, 'condition': {'weather': 'rain', 'occurs': False}}
        hotel = {'type': 'time', 'target': 'hotel_return', 'operator': '<=', 'value': '18:30',
                 'priority': 'hard', 'needs_clarification': False, 'condition': None}
        def prediction(items):
            return {'parsed_output': {'constraints': items}, 'raw_output': json.dumps({'constraints': items}),
                    'validation_errors': [], 'model_used': 'primary', 'fallback_used': False, 'attempts': []}
        first, second = prediction([weather]), prediction([hotel])
        model = Mock(); model.extract.side_effect = [first, second]
        context = {'city': 'London', 'reference_itinerary': [],
                   'change_request': 'Keep the walk if dry. Return to the hotel by 18:30.'}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); config = root / 'outputs/runtime/extractor_config.json'
            config.parent.mkdir(parents=True)
            config.write_text(json.dumps({'evidence_checks': True, 'coverage_retries': 2}))
            with patch.object(app, 'ROOT', root), patch.object(app, 'get_extractor', return_value=model):
                output = app.extract(context)
        self.assertEqual(model.extract.call_count, 2)
        self.assertEqual(output['parsed_output']['constraints'], [weather, hotel])
        self.assertEqual(output['model_parsed_output'], first['parsed_output'])
        self.assertEqual(output['raw_output'], first['raw_output'])
        self.assertEqual(output['coverage_attempts'][0]['raw_output'], second['raw_output'])
        self.assertEqual(output['coverage_unresolved'], [])


if __name__ == '__main__':
    unittest.main()
