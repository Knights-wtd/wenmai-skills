#!/usr/bin/env python3
"""Compare literal body paragraphs and direct run colors; never infer AI scores."""

import argparse
from collections import Counter
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from zipfile import BadZipFile, ZipFile

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
COLORS = ('F12828', 'F39800', '9D91E9')


def read_document(path):
    path = Path(path)
    with ZipFile(path) as archive:
        root = ET.fromstring(archive.read('word/document.xml'))
        style_names = {}
        if 'word/styles.xml' in archive.namelist():
            styles = ET.fromstring(archive.read('word/styles.xml'))
            for style in styles.findall(W + 'style'):
                name = style.find(W + 'name')
                style_names[style.get(W + 'styleId')] = name.get(W + 'val', '') if name is not None else ''
    body = root.find(W + 'body')
    if body is None:
        raise ValueError('Missing Word body')
    paragraphs = []
    for index, paragraph in enumerate(body.findall(W + 'p')):
        fragments = []
        for node in paragraph.iter():
            if node.tag == W + 't':
                fragments.append(node.text or '')
            elif node.tag == W + 'tab':
                fragments.append('\t')
            elif node.tag in (W + 'br', W + 'cr'):
                fragments.append('\n')
        style = paragraph.find('./' + W + 'pPr/' + W + 'pStyle')
        style_id = style.get(W + 'val', '') if style is not None else ''
        colors = {node.get(W + 'val', '').upper()
                  for run in paragraph.iter(W + 'r')
                  for node in run.findall('./' + W + 'rPr/' + W + 'color')}
        paragraphs.append({'index': index, 'text': ''.join(fragments),
                           'style': style_names.get(style_id, style_id),
                           'colors': sorted(colors.intersection(COLORS))})
    return {'file': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'paragraphs': paragraphs, 'direct_table_count': len(body.findall(W + 'tbl')),
            'tracked_changes_present': any(node.tag in (W + 'ins', W + 'del') for node in body.iter())}


def is_heading(style):
    normalized = style.strip().lower()
    return normalized in ('title', 'subtitle') or normalized.startswith(('heading', '标题'))


def summarize(document, start, end):
    stop = len(document['paragraphs']) if end is None else end
    selected = [p for p in document['paragraphs'][start:stop] if not is_heading(p['style'])]
    text = '\n'.join(p['text'] for p in selected)
    return {'file': document['file'], 'sha256': document['sha256'],
            'paragraph_count': len(document['paragraphs']), 'analyzed_paragraph_count': len(selected),
            'analyzed_indices': [p['index'] for p in selected],
            'marked_indices': [p['index'] for p in selected if p['colors']],
            'marked_paragraph_count': sum(bool(p['colors']) for p in selected),
            'color_paragraph_counts': dict(Counter(c for p in selected for c in p['colors'])),
            'han_characters': len(re.findall(r'[\u4e00-\u9fff]', text)),
            'direct_tables_not_analyzed': document['direct_table_count'],
            'tracked_changes_present': document['tracked_changes_present']}


def compare_documents(before, after, start=0, end=None, protected=()):
    a = [p['text'] for p in before['paragraphs']]
    b = [p['text'] for p in after['paragraphs']]
    left = summarize(before, start, end)
    right = summarize(after, start, end)
    same_count = len(a) == len(b)
    marked_left, marked_right = set(left['marked_indices']), set(right['marked_indices'])
    positional = same_count and left['analyzed_indices'] == right['analyzed_indices']
    violations = [i for i in protected if i >= len(a) or i >= len(b) or a[i] != b[i]]
    return {'comparison_kind': 'literal_text_and_direct_run_colors',
            'range': {'start_zero_based': start, 'end_exclusive': end, 'heading_styles_excluded': True},
            'before': left, 'after': right, 'same_text': a == b,
            'same_paragraph_count': same_count,
            'changed_indices_if_positionally_aligned': [i for i in range(min(len(a), len(b))) if a[i] != b[i]],
            'text_diff_ranges': [{'operation': op, 'before_start': a0, 'before_end': a1,
                                  'after_start': b0, 'after_end': b1}
                                 for op, a0, a1, b0, b1 in SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes()
                                 if op != 'equal'],
            'positional_color_comparison_available': positional,
            'newly_marked_indices_if_positionally_aligned': sorted(marked_right - marked_left) if positional else None,
            'lost_marked_indices_if_positionally_aligned': sorted(marked_left - marked_right) if positional else None,
            'protected_unchanged_indices': list(protected), 'protected_text_violations': violations,
            'limitations': ['Same paragraph count does not prove alignment; verify insertions, deletions and reordering.',
                            'Only direct body paragraphs and direct run RGB colors are analyzed.',
                            'References require an explicitly verified range; tables, images and headers are not analyzed.',
                            'Tracked revisions, if present, require manual review of visible text.',
                            'Color counts describe paragraphs, not detection scores or authorship.']}


def parse_indices(value):
    result = set()
    for item in value.split(','):
        if not item.strip():
            continue
        if ':' in item:
            lo, hi = (int(part) for part in item.split(':', 1))
            if lo < 0 or hi <= lo:
                raise ValueError('Invalid protected range')
            result.update(range(lo, hi))
        else:
            index = int(item)
            if index < 0:
                raise ValueError('Negative protected index')
            result.add(index)
    return sorted(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before', type=Path)
    parser.add_argument('after', type=Path)
    parser.add_argument('--start', type=int, default=0, help='Zero-based body paragraph start')
    parser.add_argument('--end', type=int, help='Exclusive end; use it to exclude references')
    parser.add_argument('--expect-unchanged', default='', help='Protected indices: 12,31,36:45; ranges are end-exclusive')
    parser.add_argument('--output', type=Path, help='Write JSON here instead of stdout')
    args = parser.parse_args()
    try:
        before, after = read_document(args.before), read_document(args.after)
        minimum = min(len(before['paragraphs']), len(after['paragraphs']))
        if args.start < 0 or args.start > minimum:
            raise ValueError('Start is outside the common paragraph range')
        if args.end is not None and (args.end <= args.start or args.end > minimum):
            raise ValueError('End is outside the common paragraph range')
        result = compare_documents(before, after, args.start, args.end, parse_indices(args.expect_unchanged))
        output = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output, encoding='utf-8')
        else:
            print(output, end='')
        return 2 if result['protected_text_violations'] else 0
    except (OSError, BadZipFile, KeyError, ET.ParseError, ValueError) as error:
        print('Comparison failed: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
