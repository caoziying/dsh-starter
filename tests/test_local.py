"""Fast local checks; no API key or network needed."""

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class StarterTests(unittest.TestCase):
    def test_sequence_service(self):
        service = load(ROOT / "services/sequence_demo/app.py", "starter_sequence_service")
        result = service.analyze_sequence(">demo\nACDEFGHIKLMNPQRSTVWY")
        self.assertEqual(result["length"], 20)
        self.assertEqual(sum(result["amino_acid_counts"].values()), 20)
        with self.assertRaises(ValueError):
            service.analyze_sequence(">one\nACD\n>two\nEFG")

    def test_uniprot_input_boundary(self):
        tool = load(ROOT / "harness/tools/uniprot/server.py", "starter_uniprot")
        self.assertEqual(tool.normalize_entry("https://www.uniprot.org/uniprotkb/A5PLL7/entry"), "A5PLL7")
        with self.assertRaises(ValueError):
            tool.normalize_entry("https://example.org/uniprotkb/A5PLL7")

    def test_manifest_and_skills(self):
        manifests = list((ROOT / "harness/tools").glob("*/tool.json"))
        names = {json.loads(path.read_text(encoding="utf-8"))["server_name"] for path in manifests}
        self.assertEqual(names, {"diagnostics", "uniprot", "sequence"})
        skills = list((ROOT / "harness/skills").glob("*/SKILL.md"))
        self.assertEqual(len(skills), 2)


if __name__ == "__main__":
    unittest.main()
