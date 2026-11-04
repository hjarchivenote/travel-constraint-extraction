"""The demo exposes postprocessing separately and retains the actual model output."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch


class EvidenceDemoTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1] / 'demo/app.py'
        spec = importlib.util.spec_from_file_location('evidence_demo_test', path)
        self.app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.app)
        self.context = {'city': 'London', 'reference_itinerary': [],
                        'change_request': 'Please return to the hotel by 5:10 pm.'}
        self.payload = {'constraints': [{'type': 'time', 'target': 'hotel_return',
            'operator': '<=', 'value': '19:10', 'priority': 'hard',
            'needs_clarification': False, 'condition': None}]}
        self.result = {'parsed_output': self.payload, 'raw_output': json.dumps(self.payload),
                       'validation_errors': [], 'model_used': 'primary',
                       'fallback_used': False, 'attempts': []}

    def run_with_config(self, enabled, result):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / 'outputs/runtime/extractor_config.json'
            config.parent.mkdir(parents=True)
            config.write_text(json.dumps({'evidence_checks': enabled}))
            model = Mock()
            model.extract.return_value = result
            with patch.object(self.app, 'ROOT', root), patch.object(self.app, 'get_extractor', return_value=model):
                actual = self.app.extract(self.context)
            model.extract.assert_called_once_with(self.context)
            return actual

    def test_enabled_corrects_clock_preserves_raw_output_and_model_payload(self):
        original = copy.deepcopy(self.result)
        actual = self.run_with_config(True, self.result)
        self.assertEqual(actual['parsed_output']['constraints'][0]['value'], '17:10')
        self.assertEqual(actual['raw_output'], original['raw_output'])
        self.assertEqual(actual['model_parsed_output'], original['parsed_output'])
        self.assertEqual(self.result, original)
        self.assertTrue(actual['normalization_audit'])

    def test_disabled_preserves_existing_pipeline(self):
        actual = self.run_with_config(False, self.result)
        self.assertIs(actual, self.result)

    def test_failed_model_remains_a_failure(self):
        failed = self.result | {'parsed_output': None, 'raw_output': 'broken',
                                'validation_errors': ['Invalid JSON']}
        actual = self.run_with_config(True, failed)
        self.assertIsNone(actual['parsed_output'])
        self.assertEqual(actual['raw_output'], 'broken')
        self.assertEqual(actual['validation_errors'], ['Invalid JSON'])
        self.assertEqual(actual['normalization_audit'], [])


if __name__ == '__main__':
    unittest.main()
