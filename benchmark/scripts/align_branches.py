#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
align_branches.py

Ensure each public task's must_cover_branches exactly matches the branch labels
in the private gold standard's must_find_papers. This is required because the
grader does exact (case-insensitive) branch matching.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = ROOT / "public" / "tasks"
GOLD_PATH = ROOT / "private-gold" / "gold.json"


def main() -> int:
    if not GOLD_PATH.exists():
        print(f"Error: private gold file not found: {GOLD_PATH}", file=sys.stderr)
        print("This maintenance script requires benchmark/private-gold/gold.json, which is not shipped in public releases.", file=sys.stderr)
        return 1
    try:
        with GOLD_PATH.open("r", encoding="utf-8") as fh:
            gold = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Error: could not load private gold file {GOLD_PATH}: {exc}", file=sys.stderr)
        return 1

    updated = 0
    for task_path in sorted(TASKS_DIR.glob("E*.json")):
        try:
            task = json.loads(task_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Warning: skipping unreadable task {task_path}: {exc}", file=sys.stderr)
            continue
        tid = task["id"]

        if task.get("domain_type") == "boundary":
            continue

        gold_entry = gold.get("tasks", {}).get(tid, {})
        gold_branches = [
            p.get("branch", "")
            for p in gold_entry.get("must_find_papers", [])
            if p.get("branch")
        ]

        if not gold_branches:
            print(f"Warning: no gold branches for {tid}")
            continue

        old_branches = task.get("constraints", {}).get("must_cover_branches", [])
        if old_branches != gold_branches:
            task.setdefault("constraints", {})["must_cover_branches"] = gold_branches
            task_path.write_text(
                json.dumps(task, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            print(f"Updated {tid}: {len(gold_branches)} branches")
            updated += 1
        else:
            print(f"OK {tid}: {len(gold_branches)} branches")

    print(f"\nAligned {updated} task file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
