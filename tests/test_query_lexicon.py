import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/wenmai-writing/scripts/query_lexicon.py"
spec = importlib.util.spec_from_file_location("lexicon", SCRIPT)
lexicon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lexicon)


def entry(identifier="r0001", expression="核对", genre="学术综述"):
    return {"id": identifier, "expression": expression, "kind": "书面词", "function": "版本比较",
            "meaning": "对照材料检查是否一致", "collocations": ["核对版本"], "genres": [genre],
            "example": "引用之前应核对版本。", "avoid": "核对不等于证明主张成立。", "provenance": "editorial"}


class LexiconTests(unittest.TestCase):
    def test_duplicate_expression_normalized_across_files(self):
        with tempfile.TemporaryDirectory() as directory:
            for name, item in (("one", entry()), ("two", entry("r0002", " 核 对 "))):
                Path(directory, name + ".jsonl").write_text(json.dumps(item, ensure_ascii=False) + "\n", encoding="utf-8")
            _, errors = lexicon.load_entries(Path(directory))
            self.assertTrue(any("重复 expression" in error for error in errors))

    def test_non_objects_and_malformed_fields_are_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            invalid = entry()
            invalid.update(genres=[{}], kind=["高级"], collocations=[])
            Path(directory, "bad.jsonl").write_text("[]\n{broken\n" + json.dumps(invalid) + "\n", encoding="utf-8")
            items, errors = lexicon.load_entries(Path(directory))
            self.assertEqual(items, [])
            self.assertGreaterEqual(len(errors), 4)

    def test_id_shape_and_collocation_limit_are_enforced(self):
        with tempfile.TemporaryDirectory() as directory:
            invalid = entry("arbitrary")
            invalid["collocations"] = ["核对版本", "核对引文", "核对日期", "核对作者"]
            Path(directory, "research.jsonl").write_text(json.dumps(invalid) + "\n", encoding="utf-8")
            _, errors = lexicon.load_entries(Path(directory))
            self.assertTrue(any("id 必须" in error for error in errors))
            self.assertTrue(any("1—3" in error for error in errors))

    def test_id_must_match_bank_prefix(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "literary.jsonl").write_text(json.dumps(entry()) + "\n", encoding="utf-8")
            _, errors = lexicon.load_entries(Path(directory))
            self.assertTrue(any("前缀与分库不符" in error for error in errors))

    def test_genre_filter_and_caution_does_not_recommend_term(self):
        research = entry()
        literary = entry("l0001", "清寂", "散文")
        literary.update(function="环境描写", meaning="安静而冷清", collocations=["清寂的庭院"],
                        example="庭院在暮色里渐渐清寂。", avoid="不能用于论据证明。")
        self.assertEqual(lexicon.search([research, literary], "核对", "学术综述"), [research])
        self.assertEqual(lexicon.search([research, literary], "证明"), [])
        self.assertEqual(lexicon.search([literary], genre="技术报告"), [])

    def test_cli_rejects_invalid_corpus_without_searching(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "bad.jsonl").write_text("{}\n", encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPT), "--data-dir", directory, "--query", "核对"],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(json.loads(result.stdout)["valid"])

    def test_meaning_match_precedes_incidental_example_match(self):
        relevant = entry("r0001", "据以")
        relevant.update(function="说明判断根据", meaning="用此前材料作为依据", collocations=["据以推断"],
                        example="这份记录不足以据以推断全貌。")
        incidental = entry("a0001", "厚此薄彼")
        incidental.update(function="评价不同待遇", meaning="偏爱一方而轻视另一方", collocations=["对不同对象厚此薄彼"],
                          example="不应无合理依据地厚此薄彼。")
        self.assertEqual(lexicon.search([incidental, relevant], "依据"), [relevant, incidental])


if __name__ == "__main__":
    unittest.main()
