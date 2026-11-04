"""Saved examples must not acquire a dependency on locally installed models."""

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


class SavedDemoTests(unittest.TestCase):
    def test_model_description_works_without_runtime_model_files(self):
        app_path = Path(__file__).resolve().parents[1] / "demo/app.py"
        spec = importlib.util.spec_from_file_location("project_demo_test", app_path)
        app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app)
        with tempfile.TemporaryDirectory() as empty:
            with patch.object(app, "ROOT", Path(empty)), patch.object(app, "get_extractor") as load:
                self.assertEqual(app.extractor_description(), "Qwen2.5-0.5B-Instruct + LoRA")
                load.assert_not_called()


if __name__ == "__main__":
    unittest.main()
