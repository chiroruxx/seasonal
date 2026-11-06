import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


SPEC = importlib.util.spec_from_file_location("validate_data", Path(__file__).parents[1] / "scripts/validate_data.py")
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class ResearchValidationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "raw").mkdir()
        (self.root / "raw/source.txt").write_text("11月下旬から2月上旬", encoding="utf-8")
        (self.root / "summary.md").write_text("# 調査\n\n出典1件、観測2件、不明点0件。\n", encoding="utf-8")
        self.source = {
            "schema_version": 1, "source_id": "source-1", "url": None,
            "publisher": None, "title": "資料", "retrieved_at": "2026-11-07T12:00:00+09:00",
            "updated_at": None, "terms": None, "original_path": "raw/source.txt",
            "original_unavailable_reason": None, "locator": "表1",
        }
        self.observation = {
            "schema_version": 1, "observation_id": "obs-1", "source_id": "source-1",
            "locator": "表1", "food": "ねぎ", "region": None, "origin": None,
            "variety": None, "cultivation": None, "definition": None,
            "raw_season": "11月下旬から2月上旬",
            "period": {"start": {"month": 11, "part": "late"}, "end": {"month": 2, "part": "early"}},
            "transformation": "原文の旬単位と年またぎを保持",
        }
        self.write("sources.jsonl", [self.source])
        other = {**self.observation, "observation_id": "obs-2", "raw_season": [4, 5, 9], "period": [[4, 5], [9]]}
        self.write("observations.jsonl", [self.observation, other])
        self.write("issues.jsonl", [])

    def write(self, name, records):
        (self.root / name).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")

    def errors(self):
        return validator.validate_dataset(self.root)[1]

    def test_mixed_granularity_cross_year_and_unknown_metadata_are_preserved(self):
        before = (self.root / "observations.jsonl").read_bytes()
        counts, errors = validator.validate_dataset(self.root)
        self.assertEqual([], errors)
        self.assertEqual(2, counts["observations.jsonl"])
        self.assertEqual(before, (self.root / "observations.jsonl").read_bytes())

    def test_missing_files_and_required_fields_are_not_silently_valid(self):
        del self.source["terms"]
        self.write("sources.jsonl", [self.source])
        (self.root / "issues.jsonl").unlink()
        (self.root / "summary.md").unlink()
        errors = "\n".join(self.errors())
        self.assertIn("missing terms", errors)
        self.assertIn("required file is missing", errors)
        self.assertIn("summary.md is missing", errors)

    def test_duplicate_ids_and_invalid_source_reference(self):
        self.write("sources.jsonl", [self.source, self.source])
        self.write("observations.jsonl", [{**self.observation, "source_id": "missing"}])
        errors = "\n".join(self.errors())
        self.assertIn("duplicate source_id", errors)
        self.assertIn("unknown ID", errors)

    def test_invalid_json_versions_and_empty_values(self):
        self.write("sources.jsonl", [{**self.source, "schema_version": True, "title": ""}])
        (self.root / "issues.jsonl").write_text('{"issue_id":"a","issue_id":"b"}\n[]\n{"schema_version":NaN}\n', encoding="utf-8")
        errors = "\n".join(self.errors())
        self.assertIn("schema_version must be 1", errors)
        self.assertIn("cannot be an empty string", errors)
        self.assertIn("duplicate object key", errors)
        self.assertIn("each line must be an object", errors)
        self.assertIn("non-JSON constant", errors)

    def test_retrieval_timestamp_requires_a_timezone(self):
        self.write("sources.jsonl", [{**self.source, "retrieved_at": "2026-11-07T12:00:00"}])
        self.assertTrue(any("timestamp with timezone" in e for e in self.errors()))

    def test_missing_original_requires_reason_and_saved_original_requires_file(self):
        self.write("sources.jsonl", [{**self.source, "original_path": None}])
        self.assertTrue(any("original_unavailable_reason is required" in e for e in self.errors()))
        self.write("sources.jsonl", [{**self.source, "original_path": None, "original_unavailable_reason": "保存不可"}])
        self.assertEqual([], self.errors())
        self.write("sources.jsonl", [{**self.source, "original_path": "raw/missing.txt"}])
        self.assertTrue(any("missing or escapes" in e for e in self.errors()))

    def test_original_paths_reject_traversal_and_symlink_escape(self):
        self.write("sources.jsonl", [{**self.source, "original_path": "raw/../summary.md"}])
        self.assertTrue(any("stay within raw" in e for e in self.errors()))
        (self.root / "raw/link.txt").symlink_to(self.root / "summary.md")
        self.write("sources.jsonl", [{**self.source, "original_path": "raw/link.txt"}])
        self.assertTrue(any("missing or escapes" in e for e in self.errors()))

    def test_null_raw_season_needs_linked_issue_and_issue_references_must_exist(self):
        self.write("observations.jsonl", [{**self.observation, "raw_season": None, "period": None}])
        self.assertTrue(any("must be documented" in e for e in self.errors()))
        issue = {"schema_version": 1, "issue_id": "i-1", "kind": "unknown", "source_ids": ["source-1"],
                 "observation_ids": ["obs-1"], "detail": "判読不能", "status": "unresolved", "resolution": None}
        self.write("issues.jsonl", [issue])
        self.assertEqual([], self.errors())
        self.write("issues.jsonl", [{**issue, "observation_ids": ["not-there"]}])
        self.assertTrue(any("unknown ID" in e for e in self.errors()))

    def test_discovery_separates_research_from_configuration_and_unsupported_app_data(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        (self.root / "package.json").write_text("{}", encoding="utf-8")
        assets = self.root / "app/src/main/assets"
        assets.mkdir(parents=True)
        (assets / "foods.json").write_text("[]", encoding="utf-8")
        datasets, errors = validator.discover(self.root)
        self.assertEqual([self.root.resolve()], datasets)
        self.assertEqual(1, len(errors))
        self.assertIn("app data schema is not defined", errors[0])
        (assets / "foods.json").unlink()
        self.assertEqual([], validator.discover(self.root)[1])


if __name__ == "__main__":
    unittest.main()
