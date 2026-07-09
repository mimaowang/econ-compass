#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_benchmark.py

Run the econ-compass benchmark.

Modes
-----
* ``simulate`` (default): Generate synthetic with-skill / without-skill outputs
  from the private gold standard so the scoring pipeline can be validated
  without calling an external LLM.
* ``live``: Call an external LLM executor. The executor command is pluggable
  via the ``--executor`` argument and is required in live mode.

Usage
-----
    python benchmark/scripts/run_benchmark.py --mode simulate --iterations 3
    python benchmark/scripts/run_benchmark.py --mode live --executor ./my_executor.sh --iterations 3
"""

from __future__ import annotations

import argparse
import json
import os
import random
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Allow the script to be run directly or as a module.
try:
    from .grade_output import grade_output
except ImportError:  # pragma: no cover
    from grade_output import grade_output


ROOT = Path(__file__).resolve().parent.parent.parent
BENCHMARK_ROOT = ROOT / "benchmark"
TASKS_DIR = BENCHMARK_ROOT / "public" / "tasks"
PARAPHRASE_TASKS_DIR = BENCHMARK_ROOT / "public" / "tasks-paraphrase"
GOLD_PATH = BENCHMARK_ROOT / "private-gold" / "gold.json"
WORKSPACE_DIR = BENCHMARK_ROOT / "workspace"


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Warning: could not load JSON from {path}: {exc}", file=sys.stderr)
        return None


def _discover_tasks(include_paraphrases: bool = False) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    task_dirs = [TASKS_DIR]
    if include_paraphrases:
        task_dirs.append(PARAPHRASE_TASKS_DIR)

    for task_dir in task_dirs:
        if not task_dir.exists():
            continue
        for path in sorted(task_dir.glob("E*.json")):
            task = _load_json(path)
            if isinstance(task, dict):
                task["_task_path"] = str(path)
                tasks.append(task)
    return tasks


def _make_run_dir(task_id: str, config: str, iteration: int) -> Path:
    run_dir = WORKSPACE_DIR / f"iteration-{iteration:03d}" / task_id / config
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


# ---------------------------------------------------------------------------
# Simulate mode: synthetic outputs derived from gold standard
# ---------------------------------------------------------------------------


def _render_simulated_paper(
    paper: dict[str, Any],
    language: str,
    quality: str,
    include_decoy: bool = False,
) -> str:
    """Render one paper section for a simulated output."""
    title = paper.get("title", "")
    authors = "; ".join(paper.get("authors", []))
    year = paper.get("year", "")
    journal = paper.get("journal", "")
    doi = paper.get("doi", "")
    branch = paper.get("branch", "")

    if language == "zh":
        summary = f"本研究探讨了{branch}领域的核心问题，使用严谨的方法得出了重要结论。"
        if quality == "high":
            irreplaceable = (
                f"这篇论文首次在{branch}领域建立了可检验的实证框架，提出了被后续研究广泛采用的方法。"
                f"它通过严谨的数据分析得出了具有政策含义的结论，并推动了后续一系列理论发展和实证检验。"
                f"如果删除这篇论文，{branch}领域的理论与实证研究将出现明显断层，因此它是不可替代的。"
            )
        else:
            irreplaceable = "这是一篇非常重要且被广泛引用的论文，对该领域产生了深远影响。"
    else:
        summary = f"This paper addresses a core question in {branch} using rigorous methods."
        if quality == "high":
            irreplaceable = (
                f"This paper introduced the empirical framework that defines modern research on {branch}. "
                f"No other paper combines the same theoretical insight, identification strategy, and influence on subsequent work."
            )
        else:
            irreplaceable = "This is a very important and highly cited paper that has influenced many researchers."

    return f"""## Paper 1: {title}

- **Authors**: {authors}
- **Year**: {year}
- **Journal**: {journal}
- **DOI**: {doi}
- **Core Branch/Cluster**: {branch}

### Summary
{summary}

### Why This Paper Is Irreplaceable
{irreplaceable}

"""


def _render_simulated_output(
    task: dict[str, Any],
    config: str,
    gold_task: dict[str, Any] | None,
) -> tuple[str, str]:
    """Return (markdown, bibtex) for a simulated run."""
    language = task.get("expected_output_language", "en")
    quality = "high" if config == "with_skill" else "low"
    expected_n = task.get("expected_n") or 10

    if gold_task is None:
        papers: list[dict[str, Any]] = []
    else:
        papers = gold_task.get("must_find_papers", [])

    # Determine how many papers to include.
    if config == "with_skill":
        n_papers = expected_n
    else:
        # Baseline is sloppy on count.
        n_papers = max(1, expected_n - random.choice([1, 2, 2, 3]))

    if config == "with_skill":
        # High-quality: use must_find papers, fill with acceptable alternatives if needed.
        selected = papers[:n_papers]
        alts = gold_task.get("acceptable_alternatives", []) if gold_task else []
        while len(selected) < n_papers and alts:
            alt = random.choice(alts)
            if alt not in selected:
                selected.append(alt)
    else:
        # Baseline: mix of must_find, acceptable alternatives, and decoys.
        selected = []
        must = list(papers)
        alts = list(gold_task.get("acceptable_alternatives", [])) if gold_task else []
        decoys = list(gold_task.get("forbidden_decoys", [])) if gold_task else []

        # Composition: 40% must, 30% alt, 30% decoy (simulating a weaker baseline).
        for _ in range(n_papers):
            bucket = random.choices(
                ["must", "alt", "decoy"],
                weights=[40, 30, 30] if decoys else [60, 40, 0],
                k=1
            )[0]
            if bucket == "must" and must:
                selected.append(must.pop(0) if must else random.choice(papers))
            elif bucket == "alt" and alts:
                selected.append(alts.pop(random.randrange(len(alts))))
            elif bucket == "decoy" and decoys:
                selected.append(decoys.pop(random.randrange(len(decoys))))
            elif must:
                selected.append(must.pop(0))
            elif alts:
                selected.append(alts.pop(random.randrange(len(alts))))

    # Deduplicate by title.
    seen = set()
    deduped = []
    for p in selected:
        key = p.get("title", "").lower()
        if key and key not in seen:
            seen.add(key)
            deduped.append(p)
    selected = deduped

    # Boundary tasks should not produce a reading list.
    task_id = task.get("id", "")
    if task.get("domain_type") == "boundary":
        if config == "with_skill":
            return "I can help you with that, but this request is outside the scope of curated economics reading lists.", ""
        else:
            return "I'm not sure how to answer that.", ""

    # Header
    domain_name = task.get("name", "Selected Domain")
    header_lines = [
        f"# {domain_name} — Essential Reading List",
        f"> Curated on {datetime.now(timezone.utc).strftime('%Y-%m-%d')}. N = {len(selected)} papers selected for foundational importance.",
        "> Selection follows the econ-compass methodology." if config == "with_skill" else "> Papers selected based on general knowledge.",
        "",
    ]

    if config == "with_skill" and task.get("constraints", {}).get("pdf_download") == "skip_explicit":
        header_lines.append("> [PDF download skipped per user request.]")
        header_lines.append("")

    body_lines = []
    for i, paper in enumerate(selected, start=1):
        section = _render_simulated_paper(paper, language, quality)
        # Fix the paper number in the heading.
        section = section.replace("## Paper 1:", f"## Paper {i}:")
        body_lines.append(section)

    # Selection Notes (only with_skill produces them properly; baseline omits or is minimal).
    if config == "with_skill":
        branches = [p.get("branch", "") for p in selected if p.get("branch")]
        # Compute journal distribution.
        journal_counts: dict[str, int] = {}
        for p in selected:
            j = p.get("journal", "Various")
            # Use common abbreviations for canonical journals.
            abbr = j
            if "American Economic Review" in j:
                abbr = "AER"
            elif "Quarterly Journal of Economics" in j:
                abbr = "QJE"
            elif "Journal of Political Economy" in j:
                abbr = "JPE"
            elif "Econometrica" in j:
                abbr = "Econometrica"
            elif "Review of Economic Studies" in j:
                abbr = "RES"
            elif "Journal of Development Economics" in j:
                abbr = "JDE"
            elif "Journal of Public Economics" in j:
                abbr = "JPubE"
            elif "Journal of Econometrics" in j:
                abbr = "J. Econometrics"
            elif "经济研究" in j:
                abbr = "经济研究"
            elif "经济学（季刊）" in j or "经济学" in j:
                abbr = "经济学（季刊）"
            journal_counts[abbr] = journal_counts.get(abbr, 0) + 1

        body_lines.append("## Selection Notes")
        body_lines.append("")
        body_lines.append(f"**Covered Branches/Clusters:** {', '.join(branches)}")
        body_lines.append("")
        body_lines.append("**Balance:** The selected papers span classic and contemporary work, mix theoretical frameworks with empirical identification, and include both reduced-form and structural contributions where appropriate.")
        body_lines.append("")
        body_lines.append("**Journal Distribution:**")
        body_lines.append("| Journal (Abbreviation) | Count |")
        body_lines.append("|------------------------|-------|")
        for abbr, count in sorted(journal_counts.items(), key=lambda x: -x[1]):
            body_lines.append(f"| {abbr} | {count} |")
        body_lines.append("")
        body_lines.append("**Validation Sources:**")
        body_lines.append("- Reviewed PhD field exam syllabi from MIT, Harvard, Princeton, Stanford, and Chicago.")
        body_lines.append("- Consulted Handbook chapters: Handbook of Development Economics, Handbook of Labor Economics, and Handbook of Behavioral Economics.")
        body_lines.append("- Referenced canonical reading lists and JEL/JEP survey articles for each subfield.")
        body_lines.append("- Cross-checked citations and awards (e.g., AER best paper, JBC Medal, Clark Medal).")
        body_lines.append("")
        body_lines.append("**Alternative Candidates Considered and Rejected:**")
        body_lines.append("| Paper | Why Rejected | Replaced By |")
        body_lines.append("|-------|-------------|-------------|")
        # Use real alternatives when available.
        alts = list(gold_task.get("acceptable_alternatives", [])) if gold_task else []
        decoys = list(gold_task.get("forbidden_decoys", [])) if gold_task else []
        for idx in range(min(3, max(len(alts), 1))):
            if idx < len(alts):
                alt = alts[idx]
                alt_title = alt.get("title", "Alternative paper")
                reason = f"Covers similar ground as the selected {alt.get('branch', 'branch')} paper but is narrower or later in origin."
                replaced = f"Paper {idx + 1}"
            else:
                alt_title = decoys[idx % len(decoys)].get("title", "Alternative paper") if decoys else "Other candidate"
                reason = "Classified as a textbook, survey, or off-topic work; not a canonical research article."
                replaced = "N/A"
            body_lines.append(f"| {alt_title} | {reason} | {replaced} |")
        body_lines.append("")
        body_lines.append("**Bundled Tools Used:** Generated BibTeX with `scripts/generate_bibtex.py`; validated output with `scripts/validate_output.py`.")
        body_lines.append("")

    # Interaction questions
    if task.get("domain_type") != "boundary":
        if task.get("constraints", {}).get("pdf_download") == "ask":
            if language == "zh":
                body_lines.append("是否需要我帮你下载这些论文的 PDF 原文？")
            else:
                body_lines.append("Would you like me to download the PDFs of these papers?")
        if language == "zh" and task.get("constraints", {}).get("chinese_literature_question"):
            body_lines.append("是否需要同时检索中文经济学文献（如《经济研究》《管理世界》等）？")

    markdown = "\n".join(header_lines + body_lines)

    # BibTeX
    bibtex_lines = [f"% {domain_name} — Essential Reading List", "% Generated by econ-compass benchmark simulation", ""]
    if config == "with_skill":
        used_keys: set[str] = set()
        for i, paper in enumerate(selected, start=1):
            raw_first = paper.get("authors", ["Unknown"])[0].split(",")[0].strip().lower().replace(" ", "").replace("-", "")
            # Strip non-alphabetic tail from last name when authors use initials.
            first_author = "".join(ch for ch in raw_first if ch.isalpha())
            base_key = f"{first_author}{paper.get('year', '0000')}"
            key = base_key
            suffix = "a"
            while key in used_keys:
                key = f"{base_key}{suffix}"
                suffix = chr(ord(suffix) + 1)
            used_keys.add(key)
            authors = " and ".join(paper.get("authors", []))
            bibtex_lines.append(f"@article{{{key},")
            bibtex_lines.append(f"  title   = {{{paper.get('title', '')}}},")
            bibtex_lines.append(f"  author  = {{{authors}}},")
            bibtex_lines.append(f"  journal = {{{paper.get('journal', '')}}},")
            bibtex_lines.append(f"  year    = {{{paper.get('year', '')}}},")
            if paper.get("doi"):
                bibtex_lines.append(f"  doi     = {{{paper.get('doi', '')}}}")
            bibtex_lines.append("}")
            bibtex_lines.append("")
    else:
        # Baseline often has malformed or missing BibTeX.
        roll = random.random()
        if roll < 0.35:
            bibtex_lines.append("% No BibTeX generated")
        elif roll < 0.6:
            # Malformed: missing closing braces.
            bibtex_lines.append("@article{incomplete,")
            bibtex_lines.append("  title = {No closing brace")
            bibtex_lines.append("")
        else:
            # Present but lower quality.
            for paper in selected:
                bibtex_lines.append(f"@article{{dummy,")
                bibtex_lines.append(f"  title = {{{paper.get('title', '')}}},")
                bibtex_lines.append("}")

    bibtex = "\n".join(bibtex_lines)
    return markdown, bibtex


def _run_simulate(tasks: list[dict[str, Any]], iterations: int, seed: int) -> dict[str, Any]:
    random.seed(seed)
    gold = _load_json(GOLD_PATH)
    run_manifest: list[dict[str, Any]] = []

    for iteration in range(1, iterations + 1):
        for task in tasks:
            task_id = str(task.get("id"))
            base_task_id = task_id.split("-", 1)[0]
            gold_task = gold.get("tasks", {}).get(base_task_id) if isinstance(gold, dict) else None
            task_path = Path(task.get("_task_path", TASKS_DIR / f"{base_task_id}.json"))
            for config in ("with_skill", "without_skill"):
                run_dir = _make_run_dir(task_id, config, iteration)
                md_path = run_dir / "output.md"
                bib_path = run_dir / "output.bib"

                md_text, bib_text = _render_simulated_output(task, config, gold_task)
                md_path.write_text(md_text, encoding="utf-8")
                bib_path.write_text(bib_text, encoding="utf-8")

                grading = grade_output(
                    task_path=task_path,
                    output_path=md_path,
                    gold_path=GOLD_PATH,
                    configuration=config,
                    bib_path=bib_path,
                )
                grading_path = run_dir / "grading.json"
                grading_path.write_text(json.dumps(grading, indent=2, ensure_ascii=False), encoding="utf-8")

                run_manifest.append({
                    "iteration": iteration,
                    "task_id": task_id,
                    "configuration": config,
                    "run_dir": str(run_dir.relative_to(BENCHMARK_ROOT)),
                    "total_score": grading["total_score"],
                })

    return {"mode": "simulate", "iterations": iterations, "runs": run_manifest}


# ---------------------------------------------------------------------------
# Live mode: call an external LLM executor
# ---------------------------------------------------------------------------


def _run_live(
    tasks: list[dict[str, Any]],
    iterations: int,
    executor: str,
    skill_path: Path,
) -> dict[str, Any]:
    """Run tasks against an external LLM executor."""
    run_manifest: list[dict[str, Any]] = []

    for iteration in range(1, iterations + 1):
        for task in tasks:
            task_id = str(task.get("id"))
            base_task_id = task_id.split("-", 1)[0]
            task_path = Path(task.get("_task_path", TASKS_DIR / f"{base_task_id}.json"))
            for config in ("with_skill", "without_skill"):
                run_dir = _make_run_dir(task_id, config, iteration)
                md_path = run_dir / "output.md"

                env = os.environ.copy()
                env["EC_BENCHMARK_TASK"] = str(task_path)
                env["EC_BENCHMARK_CONFIG"] = config
                env["EC_BENCHMARK_SKILL_PATH"] = str(skill_path)
                env["EC_BENCHMARK_OUTPUT"] = str(md_path)

                try:
                    subprocess.run(
                        shlex.split(executor),
                        env=env,
                        check=True,
                        capture_output=True,
                        text=True,
                        timeout=300,
                    )
                except subprocess.TimeoutExpired:
                    md_path.write_text("# Timeout\nThe executor did not finish within 300 seconds.", encoding="utf-8")
                except subprocess.CalledProcessError as exc:
                    md_path.write_text(f"# Executor Error\n{exc.stderr or exc.stdout}", encoding="utf-8")
                except (OSError, ValueError) as exc:
                    md_path.write_text(f"# Executor Error\nCould not start executor: {exc}", encoding="utf-8")

                grading = grade_output(
                    task_path=task_path,
                    output_path=md_path,
                    gold_path=GOLD_PATH,
                    configuration=config,
                )
                grading_path = run_dir / "grading.json"
                grading_path.write_text(json.dumps(grading, indent=2, ensure_ascii=False), encoding="utf-8")

                run_manifest.append({
                    "iteration": iteration,
                    "task_id": task_id,
                    "configuration": config,
                    "run_dir": str(run_dir.relative_to(BENCHMARK_ROOT)),
                    "total_score": grading["total_score"],
                })

    return {"mode": "live", "iterations": iterations, "runs": run_manifest}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the econ-compass benchmark.")
    parser.add_argument("--mode", choices=["simulate", "live"], default="simulate",
                        help="Run mode (default: simulate)")
    parser.add_argument("--iterations", type=int, default=3,
                        help="Number of repeated runs per task/configuration")
    parser.add_argument("--executor", default="",
                        help="Shell command for live-mode LLM executor")
    parser.add_argument("--skill-path", type=Path, default=ROOT,
                        help="Path to the econ-compass skill directory (for live mode)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for simulate mode")
    parser.add_argument("--clean", action="store_true",
                        help="Delete previous iteration directories before running")
    parser.add_argument("--include-paraphrases", action="store_true",
                        help="Also run public paraphrase tasks from benchmark/public/tasks-paraphrase")
    args = parser.parse_args()

    tasks = _discover_tasks(args.include_paraphrases)
    if not tasks:
        print("No tasks found in", TASKS_DIR, file=sys.stderr)
        return 1

    if args.clean:
        shutil.rmtree(WORKSPACE_DIR, ignore_errors=True)
        WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

    if args.mode == "simulate":
        manifest = _run_simulate(tasks, args.iterations, args.seed)
    else:
        if not args.executor:
            print("--executor is required for live mode", file=sys.stderr)
            return 1
        manifest = _run_live(tasks, args.iterations, args.executor, args.skill_path)

    manifest_path = WORKSPACE_DIR / f"iteration-{args.iterations:03d}" / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Benchmark complete. Manifest written to {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
