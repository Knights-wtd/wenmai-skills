import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/wenmai-feedback/scripts/compare_docx_reports.py'
spec = importlib.util.spec_from_file_location('compare_docx_reports', SCRIPT)
compare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compare)
W = compare.W


def write_docx(path, paragraphs):
    root = ET.Element(W + 'document')
    body = ET.SubElement(root, W + 'body')
    for data in paragraphs:
        p = ET.SubElement(body, W + 'p')
        if data.get('style'):
            ET.SubElement(ET.SubElement(p, W + 'pPr'), W + 'pStyle', {W + 'val': data['style']})
        for text, color in data.get('runs', [(data.get('text', ''), None)]):
            r = ET.SubElement(p, W + 'r')
            props = ET.SubElement(r, W + 'rPr')
            ET.SubElement(props, W + 'highlight', {W + 'val': 'none'})
            if color:
                ET.SubElement(props, W + 'color', {W + 'val': color})
            ET.SubElement(r, W + 't').text = text
    styles = ET.Element(W + 'styles')
    style = ET.SubElement(styles, W + 'style', {W + 'styleId': 'h1'})
    ET.SubElement(style, W + 'name', {W + 'val': 'heading 1'})
    with ZipFile(path, 'w') as archive:
        archive.writestr('word/document.xml', ET.tostring(root, encoding='utf-8'))
        archive.writestr('word/styles.xml', ET.tostring(styles, encoding='utf-8'))


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.before, self.after = self.root / 'before.docx', self.root / 'after.docx'

    def tearDown(self):
        self.temp.cleanup()

    def test_split_runs_and_none_highlight_preserve_identity(self):
        write_docx(self.before, [{'text': '可能改善[1]'}])
        write_docx(self.after, [{'runs': [('可能', 'F12828'), ('改善[1]', 'F12828')]}])
        result = compare.compare_documents(compare.read_document(self.before), compare.read_document(self.after))
        self.assertTrue(result['same_text'])
        self.assertEqual(result['after']['color_paragraph_counts'], {'F12828': 1})
        self.assertEqual(result['newly_marked_indices_if_positionally_aligned'], [0])

    def test_heading_and_references_do_not_pollute_selected_range(self):
        paragraphs = [{'style': 'h1', 'runs': [('标题', 'F12828')]},
                      {'runs': [('正文', 'F39800')]},
                      {'runs': [('检索式', 'B0B0B0')]},
                      {'runs': [('参考文献[1]', 'F12828')]}]
        write_docx(self.before, paragraphs)
        result = compare.summarize(compare.read_document(self.before), 0, 3)
        self.assertEqual(result['analyzed_indices'], [1, 2])
        self.assertEqual(result['marked_paragraph_count'], 1)
        self.assertEqual(result['color_paragraph_counts'], {'F39800': 1})

    def test_inserted_paragraph_disables_positional_color_attribution(self):
        write_docx(self.before, [{'text': '正文'}, {'text': '公式'}])
        write_docx(self.after, [{'text': '图注'}, {'runs': [('正文', 'F12828')]}, {'text': '公式'}])
        result = compare.compare_documents(compare.read_document(self.before), compare.read_document(self.after))
        self.assertFalse(result['positional_color_comparison_available'])
        self.assertIsNone(result['newly_marked_indices_if_positionally_aligned'])
        self.assertEqual(result['text_diff_ranges'][0]['operation'], 'insert')

    def test_cli_reports_protected_claim_change_as_failure(self):
        write_docx(self.before, [{'text': '可能改善'}])
        write_docx(self.after, [{'text': '已证实改善'}])
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.before), str(self.after),
                                 '--expect-unchanged', '0'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        report = json.loads(result.stdout)
        self.assertEqual(report['protected_text_violations'], [0])


if __name__ == '__main__':
    unittest.main()
