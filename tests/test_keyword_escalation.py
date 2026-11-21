import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import scipy.special


class KeywordEscalationTests(unittest.TestCase):
    def setUp(self):
        sentiment_model = Mock(return_value=[[{"label": "negative", "score": 0.9}]])
        self.nli = Mock()
        self.nli.predict.return_value = [[10.0, 0.0, 0.0]]
        transformers = types.ModuleType("transformers")
        transformers.pipeline = Mock(return_value=sentiment_model)
        sentence_transformers = types.ModuleType("sentence_transformers")
        sentence_transformers.CrossEncoder = Mock(return_value=self.nli)
        spec = importlib.util.spec_from_file_location(
            "keyword_sentiment", Path(__file__).parents[1] / "pipeline" / "sentiment.py"
        )
        self.sentiment = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {
            "transformers": transformers,
            "sentence_transformers": sentence_transformers,
        }):
            spec.loader.exec_module(self.sentiment)

    def test_contractions_keep_high_severity(self):
        for text in ["I can't breathe", "I can’t breathe", "I don't want to live", "I don’t want to live"]:
            with self.subTest(text=text):
                result = self.sentiment.analyse(text)
                self.assertEqual(result.escalation_severity, "high")
                self.assertTrue(result.escalated)
        self.nli.predict.assert_not_called()

    def test_non_keyword_input_uses_nli(self):
        self.assertIsNone(self.sentiment.analyse("I need help with medication costs").escalation_severity)
        self.nli.predict.assert_called_once()


if __name__ == "__main__":
    unittest.main()
