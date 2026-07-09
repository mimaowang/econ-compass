#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
aggregate_results.py

Aggregate per-run ``grading.json`` files into ``benchmark.json`` and a human-readable
``benchmark.md`` summary.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent


def _load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Warning: skipping unreadable grading file {path}: {exc}", file=sys.stderr)
        return None


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = _mean(values)
    variance = sum((x - m) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(variance)


def _collect_gradings(workspace_dir: Path) -> list[dict[str, Any]]:
    gradings = []
    for grading_path in sorted(workspace_dir.rglob("grading.json")):
        rel = grading_path.relative_to(workspace_dir)
        parts = rel.parts
        # Supports both:
        #   <task_id>/<config>/grading.json
        #   <iteration>/<task_id>/<config>/grading.json
        if len(parts) < 3:
            continue
        task_id, config, _ = parts[-3:]
        data = _load_json(grading_path)
        if not isinstance(data, dict):
            continue
        if config not in {"with_skill", "without_skill"}:
            print(f"Warning: skipping grading with unknown config {config}: {grading_path}", file=sys.stderr)
            continue
        data["_task_id"] = task_id
        data["_config"] = config
        gradings.append(data)
    return gradings


def _score_stats(values: list[float]) -> dict[str, float]:
    return {
        "mean": round(_mean(values), 2),
        "std": round(_std(values), 2),
        "min": round(min(values), 2) if values else 0.0,
        "max": round(max(values), 2) if values else 0.0,
        "n": len(values),
    }


def _by_task(gradings: list[dict[str, Any]]) -> dict[str, dict[str, list[float]]]:
    grouped: dict[str, dict[str, list[float]]] = {}
    for g in gradings:
        tid = g["_task_id"]
        cfg = g["_config"]
        grouped.setdefault(tid, {"with_skill": [], "without_skill": []})
        grouped[tid][cfg].append(g["total_score"])
    return grouped


def _dimension_stats(gradings: list[dict[str, Any]], config: str) -> dict[str, dict[str, float]]:
    scores_by_dim: dict[str, list[float]] = {}
    for g in gradings:
        if g["_config"] != config:
            continue
        for dim, score in g.get("scores", {}).items():
            scores_by_dim.setdefault(dim, []).append(float(score))
    return {dim: _score_stats(vals) for dim, vals in scores_by_dim.items()}


def _critical_cap_counts(gradings: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for g in gradings:
        for cap in g.get("critical_caps", []):
            if cap.get("triggered"):
                counts[cap["id"]] = counts.get(cap["id"], 0) + 1
    return counts


def _flaky_tasks(by_task: dict[str, dict[str, list[float]]], threshold: float = 15.0) -> list[str]:
    flaky = []
    for tid, configs in by_task.items():
        for cfg, scores in configs.items():
            if len(scores) >= 2 and _std(scores) > threshold:
                flaky.append(f"{tid}/{cfg} (std={_std(scores):.1f})")
    return flaky


def aggregate(workspace_dir: Path, skill_name: str = "econ-compass") -> dict[str, Any]:
    gradings = _collect_gradings(workspace_dir)
    if not gradings:
        raise ValueError(f"No grading.json files found under {workspace_dir}")

    by_config = {
        "with_skill": [g["total_score"] for g in gradings if g["_config"] == "with_skill"],
        "without_skill": [g["total_score"] for g in gradings if g["_config"] == "without_skill"],
    }

    deltas = []
    by_task_data = _by_task(gradings)
    for tid, configs in by_task_data.items():
        ws = configs.get("with_skill", [])
        wo = configs.get("without_skill", [])
        if ws and wo:
            deltas.append(_mean(ws) - _mean(wo))

    summary = {
        "with_skill": _score_stats(by_config["with_skill"]),
        "without_skill": _score_stats(by_config["without_skill"]),
        "delta": _score_stats(deltas),
        "critical_cap_violations": sum(1 for g in gradings if any(c.get("triggered") for c in g.get("critical_caps", []))),
        "critical_cap_breakdown": _critical_cap_counts(gradings),
        "flaky_evals": _flaky_tasks(by_task_data),
        "dimension_stats": {
            "with_skill": _dimension_stats(gradings, "with_skill"),
            "without_skill": _dimension_stats(gradings, "without_skill"),
        },
        "by_task": {
            tid: {
                cfg: _score_stats(scores) for cfg, scores in configs.items()
            }
            for tid, configs in by_task_data.items()
        },
    }

    manifest_path = workspace_dir / "manifest.json"
    if manifest_path.exists():
        timestamp = datetime.fromtimestamp(manifest_path.stat().st_mtime, tz=timezone.utc).isoformat()
    else:
        timestamp = datetime.now(timezone.utc).isoformat()

    benchmark = {
        "skill_name": skill_name,
        "iteration": workspace_dir.name,
        "timestamp": timestamp,
        "runs": [
            {
                "task_id": g["_task_id"],
                "configuration": g["_config"],
                "run_id": 0,  # Not tracked separately in this version
                "total_score": g["total_score"],
                "duration_ms": 0,
                "tokens": 0,
            }
            for g in gradings
        ],
        "summary": summary,
    }
    return benchmark


def _render_markdown(benchmark: dict[str, Any]) -> str:
    s = benchmark["summary"]
    ws = s["with_skill"]
    wo = s["without_skill"]
    delta = s["delta"]

    lines = [
        f"# Benchmark Report: {benchmark['skill_name']}",
        f"**Iteration:** {benchmark['iteration']}  ",
        f"**Timestamp:** {benchmark['timestamp']}  ",
        "",
        "## Aggregate Scores",
        "",
        "| Configuration | Mean | Std | Min | Max | N |",
        "|---------------|------|-----|-----|-----|---|",
        f"| with_skill | {ws['mean']} | {ws['std']} | {ws['min']} | {ws['max']} | {ws['n']} |",
        f"| without_skill | {wo['mean']} | {wo['std']} | {wo['min']} | {wo['max']} | {wo['n']} |",
        f"| **Delta** | **{delta['mean']}** | **{delta['std']}** | - | - | **{delta['n']}** |",
        "",
        "## Quality Gate",
        "",
    ]

    cap_rate = s["critical_cap_violations"] / max(ws["n"], 1)
    flaky_rate = len(s["flaky_evals"]) / max(ws["n"], 1)
    gate_pass = (
        ws["mean"] >= 80
        and wo["mean"] <= 65
        and delta["mean"] >= 15
        and flaky_rate < 0.15
        and cap_rate < 0.10
    )
    lines.append(f"**Overall gate:** {'PASS' if gate_pass else 'FAIL'}")
    lines.append("")
    lines.append(f"- with_skill mean ≥ 80: {'✅' if ws['mean'] >= 80 else '❌'} ({ws['mean']})")
    lines.append(f"- without_skill mean ≤ 65: {'✅' if wo['mean'] <= 65 else '❌'} ({wo['mean']})")
    lines.append(f"- delta ≥ +15: {'✅' if delta['mean'] >= 15 else '❌'} ({delta['mean']})")
    lines.append(f"- flaky rate < 15%: {'✅' if len(s['flaky_evals']) / max(ws['n'], 1) < 0.15 else '❌'}")
    lines.append("")

    lines.append("## Critical Cap Violations")
    lines.append("")
    lines.append(f"Total violations: {s['critical_cap_violations']}")
    lines.append("")
    if s["critical_cap_breakdown"]:
        lines.append("| Cap | Count |")
        lines.append("|-----|-------|")
        for cap_id, count in sorted(s["critical_cap_breakdown"].items(), key=lambda x: -x[1]):
            lines.append(f"| {cap_id} | {count} |")
    else:
        lines.append("No critical cap violations detected.")
    lines.append("")

    lines.append("## Dimension Breakdown (with_skill)")
    lines.append("")
    lines.append("| Dimension | Mean | Std |")
    lines.append("|-----------|------|-----|")
    for dim, stats in s["dimension_stats"]["with_skill"].items():
        lines.append(f"| {dim} | {stats['mean']} | {stats['std']} |")
    lines.append("")

    lines.append("## Per-Task Summary")
    lines.append("")
    lines.append("| Task | with_skill mean | without_skill mean | Delta |")
    lines.append("|------|-----------------|--------------------|-------|")
    for tid in sorted(s["by_task"].keys()):
        t = s["by_task"][tid]
        ws_m = t.get("with_skill", {}).get("mean", "-")
        wo_m = t.get("without_skill", {}).get("mean", "-")
        d = round(ws_m - wo_m, 2) if isinstance(ws_m, (int, float)) and isinstance(wo_m, (int, float)) else "-"
        lines.append(f"| {tid} | {ws_m} | {wo_m} | {d} |")
    lines.append("")

    if s["flaky_evals"]:
        lines.append("## Flaky Evaluations")
        lines.append("")
        for item in s["flaky_evals"]:
            lines.append(f"- {item}")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate benchmark grading results.")
    parser.add_argument("--workspace", type=Path, required=True,
                        help="Path to the workspace iteration directory")
    parser.add_argument("--skill-name", default="econ-compass",
                        help="Name of the skill being benchmarked")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    benchmark = aggregate(workspace, args.skill_name)

    json_path = workspace / "benchmark.json"
    md_path = workspace / "benchmark.md"

    json_path.write_text(json.dumps(benchmark, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(_render_markdown(benchmark), encoding="utf-8")

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
