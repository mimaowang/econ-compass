#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
leak_check.py

Scan model outputs for canary strings or gold paper titles that should only exist
in the sealed private-gold standard. Any match indicates potential data leakage.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GOLD_PATH = ROOT / "private-gold" / "gold.json"
WORKSPACE_DIR = ROOT / "workspace"


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _paper_title(paper: object) -> str:
    if isinstance(paper, dict):
        return str(paper.get("title", ""))
    return str(paper)


def _collect_sensitive_strings(gold: dict, include_titles: bool = False) -> dict[str, list[str]]:
    """Map task_id -> list of sensitive strings to watch for."""
    sensitive: dict[str, list[str]] = {}
    for tid, entry in gold.get("tasks", {}).items():
        strings = []
        if "canary" in entry:
            strings.append(entry["canary"])
        if include_titles:
            for paper in entry.get("must_find_papers", []):
                strings.append(_paper_title(paper))
            for paper in entry.get("acceptable_alternatives", []):
                strings.append(_paper_title(paper))
            for paper in entry.get("forbidden_decoys", []):
                strings.append(_paper_title(paper))
        sensitive[tid] = [s for s in strings if s]
    return sensitive


def check_leak(workspace_dir: Path, gold_path: Path, include_titles: bool = False) -> dict:
    gold = _load_json(gold_path)
    sensitive = _collect_sensitive_strings(gold, include_titles=include_titles)
    leaks: list[dict] = []

    for output_path in sorted(workspace_dir.rglob("output.md")):
        rel = output_path.relative_to(workspace_dir)
        parts = rel.parts
        if len(parts) < 3:
            continue
        tid = parts[-3]
        config = parts[-2]
        text = output_path.read_text(encoding="utf-8").lower()

        for secret in sensitive.get(tid, []):
            if secret.lower() in text:
                leaks.append({
                    "task_id": tid,
                    "configuration": config,
                    "file": str(output_path),
                    "leaked": secret[:80],
                })

    return {
        "leak_count": len(leaks),
        "leaks": leaks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check benchmark outputs for gold leakage.")
    parser.add_argument("--workspace", type=Path, default=WORKSPACE_DIR,
                        help="Path to workspace directory")
    parser.add_argument("--gold", type=Path, default=GOLD_PATH,
                        help="Path to private gold JSON")
    parser.add_argument("--include-titles", action="store_true",
                        help="Also check for gold paper titles (not just canaries)")
    args = parser.parse_args()

    result = check_leak(args.workspace, args.gold, include_titles=args.include_titles)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1 if result["leak_count"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
