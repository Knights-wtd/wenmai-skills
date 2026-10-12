#!/usr/bin/env python3
"""Validate and search the Wenmai editorial lexicon with literal matching."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
import unicodedata

DEFAULT_DIR = Path(__file__).resolve().parents[1] / "assets" / "lexicon"
FIELDS = {"id", "expression", "kind", "function", "meaning", "collocations",
          "genres", "example", "avoid", "provenance"}
KINDS = {"书面词", "成语", "四字搭配", "表达框架"}
GENRES = {"技术报告", "学术综述", "评论", "散文", "叙事"}
PREFIXES = {"research": "r", "analysis": "a", "commentary": "c", "literary": "l"}


def normalized(value: str) -> str:
    return "".join(unicodedata.normalize("NFKC", value).split()).casefold()


def load_entries(directory: Path) -> tuple[list[dict], list[str]]:
    entries, errors = [], []
    ids, expressions = {}, {}
    paths = sorted(directory.glob("*.jsonl"))
    if not paths:
        return [], [f"{directory}: 未找到 JSONL 素材文件"]
    for path in paths:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            location = f"{path.name}:{number}"
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"{location}: 无效 JSON ({exc.msg})")
                continue
            if not isinstance(entry, dict):
                errors.append(f"{location}: 条目必须为对象")
                continue
            start = len(errors)
            if set(entry) != FIELDS:
                errors.append(f"{location}: 字段不符，缺少 {sorted(FIELDS - set(entry))}，多出 {sorted(set(entry) - FIELDS)}")
            for field in FIELDS - {"collocations", "genres"}:
                value = entry.get(field)
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"{location}: {field} 必须为非空字符串")
            for field in ("collocations", "genres"):
                value = entry.get(field)
                if (not isinstance(value, list) or not value or
                        any(not isinstance(item, str) or not item.strip() for item in value)):
                    errors.append(f"{location}: {field} 必须为非空字符串数组")
                elif len(value) != len(set(value)):
                    errors.append(f"{location}: {field} 含重复项")
            identifier = entry.get("id")
            if isinstance(identifier, str):
                match = re.fullmatch(r"([racl])([0-9]{4})", identifier)
                if not match or int(match[2]) == 0:
                    errors.append(f"{location}: id 必须为 r/a/c/l 前缀及四位非零编号")
                elif path.stem in PREFIXES and match[1] != PREFIXES[path.stem]:
                    errors.append(f"{location}: id 前缀与分库不符")
            collocations = entry.get("collocations")
            if isinstance(collocations, list) and len(collocations) > 3:
                errors.append(f"{location}: collocations 只允许 1—3 项")
            if not isinstance(entry.get("kind"), str) or entry.get("kind") not in KINDS:
                errors.append(f"{location}: kind 无效")
            genres = entry.get("genres")
            if isinstance(genres, list) and all(isinstance(g, str) for g in genres):
                if not set(genres) <= GENRES:
                    errors.append(f"{location}: genres 含未知文体")
            if entry.get("provenance") != "editorial":
                errors.append(f"{location}: provenance 必须为 editorial")
            if len(errors) != start:
                continue
            for field, seen in (("id", ids), ("expression", expressions)):
                key = normalized(entry[field])
                if key in seen:
                    errors.append(f"{location}: 重复 {field} {entry[field]}，首次位于 {seen[key]}")
                else:
                    seen[key] = location
            entries.append(entry)
    return entries, errors


def search(entries: list[dict], query: str = "", genre: str | None = None,
           kind: str | None = None, function: str = "") -> list[dict]:
    terms = [normalized(term) for term in query.split() if term.strip()]
    ranked = []
    for entry in entries:
        if genre and genre not in entry["genres"]:
            continue
        if kind and kind != entry["kind"]:
            continue
        if function and normalized(function) not in normalized(entry["function"]):
            continue
        expression = normalized(entry["expression"])
        # Avoid text is a caution, not positive evidence for recommending a term.
        content = normalized(" ".join([entry["expression"], entry["function"],
                                       entry["meaning"], *entry["collocations"], entry["example"]]))
        if not all(term in content for term in terms):
            continue
        score = 0
        for term in terms:
            if term == expression:
                score += 100
            elif term in expression:
                score += 30
            else:
                score += 10 * (term in normalized(entry["function"]))
                score += 8 * (term in normalized(entry["meaning"]))
                score += 5 * (term in normalized(" ".join(entry["collocations"])))
                score += term in normalized(entry["example"])
        ranked.append((score, entry))
    ranked.sort(key=lambda item: (-item[0], item[1]["id"]))
    return [entry for _, entry in ranked]


def stats(entries: list[dict]) -> dict:
    return {"total": len(entries),
            "kinds": dict(sorted(Counter(e["kind"] for e in entries).items())),
            "genres": dict(sorted(Counter(g for e in entries for g in e["genres"]).items()))}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DIR)
    parser.add_argument("--query", default="", help="空格分隔的字面关键词，所有词都须匹配")
    parser.add_argument("--genre", choices=sorted(GENRES))
    parser.add_argument("--kind", choices=sorted(KINDS))
    parser.add_argument("--function", default="", help="写作任务的字面筛选")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args(argv)
    if args.limit < 1:
        parser.error("--limit 必须大于零")
    try:
        entries, errors = load_entries(args.data_dir)
    except (OSError, UnicodeError) as exc:
        print(f"无法读取素材库: {exc}", file=sys.stderr)
        return 2
    if errors:
        print(json.dumps({"valid": False, "errors": errors}, ensure_ascii=False, indent=2))
        return 2
    if args.validate or args.stats:
        result = stats(entries)
        if args.validate:
            result["valid"] = True
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    matches = search(entries, args.query, args.genre, args.kind, args.function)
    selected = matches[:args.limit]
    if args.json:
        print(json.dumps({"matched": len(matches), "returned": len(selected), "entries": selected},
                         ensure_ascii=False, indent=2))
    else:
        print(f"匹配 {len(matches)} 条，显示 {len(selected)} 条。例句为原创用法示范。")
        for entry in selected:
            print(f"\n[{entry['id']}] {entry['expression']}（{entry['kind']}；{'、'.join(entry['genres'])}）")
            print(f"含义：{entry['meaning']}\n搭配：{'；'.join(entry['collocations'])}")
            print(f"例句：{entry['example']}\n边界：{entry['avoid']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
