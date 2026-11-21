import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from presidio_anonymizer.entities import RecognizerResult
from pipeline.anonymiser import anonymise, restore


class RedactionContractTests(unittest.TestCase):
    def setUp(self):
        self.analyzer = Mock()
        analyzer_module = types.ModuleType("presidio_analyzer")
        analyzer_module.AnalyzerEngine = Mock(return_value=self.analyzer)
        analyzer_module.PatternRecognizer = Mock()
        analyzer_module.Pattern = Mock()
        spec = importlib.util.spec_from_file_location(
            "contract_redactor", Path(__file__).parents[1] / "pipeline" / "redactor.py"
        )
        self.redactor = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"presidio_analyzer": analyzer_module}):
            spec.loader.exec_module(self.redactor)

    def test_typed_placeholders_reach_anonymisation_and_restore(self):
        text = "Alice called Bob"
        self.analyzer.analyze.return_value = [
            RecognizerResult(entity_type="PERSON", start=0, end=5, score=0.9),
            RecognizerResult(entity_type="PERSON", start=13, end=16, score=0.9),
        ]
        redacted = self.redactor.redact(text)
        self.assertEqual(redacted.redacted, "<PERSON> called <PERSON>")
        anonymised, mapping = anonymise(redacted)
        self.assertEqual(anonymised, "[PERSON_1] called [PERSON_2]")
        self.assertEqual(mapping, {"[PERSON_1]": "Alice", "[PERSON_2]": "Bob"})
        self.assertEqual(restore(anonymised, mapping), text)

    def test_text_without_entities_is_preserved(self):
        self.analyzer.analyze.return_value = []
        self.assertEqual(anonymise(self.redactor.redact("No names here")), ("No names here", {}))


if __name__ == "__main__":
    unittest.main()
