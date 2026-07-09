#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
grade_output.py

Grade a single model output for an econ-compass benchmark task.

Usage
-----
    python benchmark/scripts/grade_output.py \
        --task benchmark/public/tasks/E001.json \
        --output workspace/iteration-001/E001/with_skill/output.md \
        --gold benchmark/private-gold/gold.json \
        --config with_skill

The script writes ``grading.json`` next to the output Markdown file.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# Try relative import first (when run as ``python -m benchmark.scripts.grade_output``),
# then absolute import (when run as ``python benchmark/scripts/grade_output.py``).
try:
    from .format_checker import check_format, extract_papers
except ImportError:  # pragma: no cover
    from format_checker import check_format, extract_papers


# ---------------------------------------------------------------------------
# Constants and heuristics
# ---------------------------------------------------------------------------

MAX_SCORES = {
    "coverage": 20.0,
    "canonical_quality": 25.0,
    "justification_quality": 20.0,
    "evidence_metadata": 10.0,
    "output_format": 10.0,
    "interaction": 15.0,
}

# Generic praise phrases that lower Justification Quality scores.
_GENERIC_PHRASES = (
    "very important",
    "very significant",
    "highly cited",
    "influential researchers",
    "influential paper",
    "very influential",
    "widely cited",
    "seminal work",
    "groundbreaking",
    "pioneering",
    "important paper",
    "crucial paper",
    "key paper",
    "landmark paper",
    "of great importance",
    "has influenced many",
    "extremely important",
    "very famous",
    "widely recognized",
    "classic paper",
)

# Placeholder / fabrication signals for metadata.
_PLACEHOLDER_VALUES = (
    "n/a",
    "na",
    "tbd",
    "todo",
    "unknown",
    "missing",
    "not available",
    "placeholder",
    "example",
    "sample",
    "待补充",
    "未知",
)


# ---------------------------------------------------------------------------
# Task / gold loading helpers
# ---------------------------------------------------------------------------


def _load_json(path: Path | None) -> dict[str, Any] | None:
    """Load a JSON file, returning None on any error."""
    if path is None or not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:  # pragma: no cover
        print(f"Warning: could not load {path}: {exc}", file=sys.stderr)
        return None


def _get_task_entry(gold: Any, task_id: str) -> dict[str, Any] | None:
    """
    Locate the gold entry for ``task_id``.

    Supports several common shapes:
        { "tasks": { "E001": {...}, ... } }
        { "E001": {...}, ... }
        [ { "id": "E001", ... }, ... ]
    """
    if not isinstance(gold, (dict, list)):
        return None

    if isinstance(gold, dict):
        if task_id in gold and isinstance(gold[task_id], dict):
            return gold[task_id]
        if "tasks" in gold and isinstance(gold["tasks"], dict):
            tasks = gold["tasks"]
            if task_id in tasks and isinstance(tasks[task_id], dict):
                return tasks[task_id]
        return None

    # List shape.
    for entry in gold:
        if isinstance(entry, dict) and entry.get("id") == task_id:
            return entry
    return None


def _normalize_paper_entry(entry: Any) -> dict[str, Any]:
    """
    Convert a gold entry (string or dict) into a normalized dict with
    ``title``, ``authors`` (list of strings), and optionally ``year``.
    """
    result: dict[str, Any] = {"title": "", "authors": [], "year": ""}
    if isinstance(entry, str):
        result["title"] = entry.strip()
        return result
    if isinstance(entry, dict):
        result["title"] = str(entry.get("title", "")).strip()
        result["year"] = str(entry.get("year", "")).strip()
        authors = entry.get("authors", [])
        if isinstance(authors, str):
            result["authors"] = [a.strip() for a in authors.split(",") if a.strip()]
        elif isinstance(authors, list):
            result["authors"] = [str(a).strip() for a in authors if str(a).strip()]
    return result


def _extract_last_names(author_texts: list[str]) -> set[str]:
    """Extract probable last names from author strings."""
    last_names: set[str] = set()
    for text in author_texts:
        # Common forms: "Acemoglu, Daron", "Daron Acemoglu", "Acemoglu D."
        parts = [p.strip().strip(",.") for p in re.split(r"[;,]", text) if p.strip()]
        for part in parts:
            tokens = part.split()
            if not tokens:
                continue
            if "," in part:
                # Last, First -> first token is last name.
                last_names.add(tokens[0].lower())
            else:
                # First Last -> last token is last name.
                last_names.add(tokens[-1].lower())
    return last_names


def _normalize_for_match(text: str) -> str:
    """Strip punctuation and lower-case a string for fuzzy comparison."""
    return re.sub(r"[^\w\s]", "", text.lower()).strip()


def _normalize_doi(doi: str) -> str:
    """Strip common DOI prefixes and surrounding whitespace."""
    if not doi:
        return ""
    doi = doi.strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi.org/", "doi:"):
        if doi.lower().startswith(prefix):
            doi = doi[len(prefix):].strip()
    return doi


def _title_matches(title_a: str, title_b: str) -> bool:
    """Fuzzy title match: substring or high token overlap."""
    a = _normalize_for_match(title_a)
    b = _normalize_for_match(title_b)
    if not a or not b:
        return False
    if a in b or b in a:
        return True
    tokens_a = set(a.split())
    tokens_b = set(b.split())
    if not tokens_a or not tokens_b:
        return False
    overlap = tokens_a & tokens_b
    # Require at least half of the shorter title's words to match.
    return len(overlap) >= min(len(tokens_a), len(tokens_b)) * 0.5


def _paper_matches_gold(paper: dict[str, Any], gold_entry: dict[str, Any]) -> bool:
    """Return True if a parsed paper matches a gold/acceptable/forbidden entry."""
    if not _title_matches(paper.get("title", ""), gold_entry.get("title", "")):
        return False

    # Year check is strict when provided.
    gold_year = str(gold_entry.get("year", "")).strip()
    if gold_year and paper.get("year") != gold_year:
        return False

    # Author check is permissive: any shared last name is enough.
    gold_authors = gold_entry.get("authors", [])
    if gold_authors:
        gold_last = _extract_last_names(gold_authors)
        paper_last = _extract_last_names(paper.get("authors", []))
        if gold_last and paper_last and not gold_last.intersection(paper_last):
            return False

    return True


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _score_coverage(
    papers: list[dict[str, Any]],
    required_branches: list[str],
    assertions: list[dict[str, Any]],
) -> float:
    """
    Coverage score (0-20).

    Every required branch must be represented by at least one paper's
    ``core_branch`` field.
    """
    if not required_branches:
        assertions.append(
            {
                "id": "coverage-no-required-branches",
                "text": "No required branches specified in task constraints.",
                "passed": True,
                "evidence": "Coverage skipped because must_cover_branches is empty.",
            }
        )
        return MAX_SCORES["coverage"]

    branches_found: set[str] = set()
    for paper in papers:
        branch = (paper.get("core_branch") or "").strip()
        if branch:
            branches_found.add(branch.lower())

    covered = 0
    for branch in required_branches:
        if branch.lower() in branches_found:
            covered += 1
            assertions.append(
                {
                    "id": f"coverage-branch-{branch}",
                    "text": f"Required branch '{branch}' is covered.",
                    "passed": True,
                    "evidence": f"Found paper(s) tagged with core branch '{branch}'.",
                }
            )
        else:
            assertions.append(
                {
                    "id": f"coverage-branch-{branch}",
                    "text": f"Required branch '{branch}' is missing.",
                    "passed": False,
                    "evidence": "No paper's core_branch matches this branch.",
                }
            )

    ratio = covered / len(required_branches)
    if ratio >= 1.0:
        score = 20.0
    elif ratio >= 0.75:
        score = 16.0
    elif ratio >= 0.5:
        score = 12.0
    elif ratio >= 0.25:
        score = 7.0
    else:
        score = 3.0
    return score


def _score_canonical_quality(
    papers: list[dict[str, Any]],
    gold_task: dict[str, Any] | None,
    assertions: list[dict[str, Any]],
) -> tuple[float, bool]:
    """
    Canonical Quality score (0-25).

    Returns (score, forbidden_present).
    """
    if not gold_task:
        assertions.append(
            {
                "id": "canonical-no-gold",
                "text": "No private gold standard available for canonical quality scoring.",
                "passed": True,
                "evidence": "Canonical quality set to neutral midpoint (12/25).",
            }
        )
        return 12.0, False

    must_find = [_normalize_paper_entry(e) for e in gold_task.get("must_find_papers", [])]
    acceptable = [
        _normalize_paper_entry(e) for e in gold_task.get("acceptable_alternatives", [])
    ]
    forbidden = [_normalize_paper_entry(e) for e in gold_task.get("forbidden_decoys", [])]

    # Must-find hits
    must_hits = 0
    matched_must_indices: set[int] = set()
    for entry_idx, entry in enumerate(must_find):
        hit = any(_paper_matches_gold(paper, entry) for paper in papers)
        if hit:
            must_hits += 1
            matched_must_indices.add(entry_idx)
            assertions.append(
                {
                    "id": f"canonical-must-{entry_idx}",
                    "text": f"Must-find paper '{entry['title']}' found.",
                    "passed": True,
                    "evidence": "Title (and year/authors when provided) matched.",
                }
            )
        else:
            assertions.append(
                {
                    "id": f"canonical-must-{entry_idx}",
                    "text": f"Must-find paper '{entry['title']}' not found.",
                    "passed": False,
                    "evidence": "No output paper matched the expected title/year/authors.",
                }
            )

    # Acceptable alternative hits
    acceptable_hits = 0
    for entry_idx, entry in enumerate(acceptable):
        hit = any(_paper_matches_gold(paper, entry) for paper in papers)
        if hit:
            acceptable_hits += 1
            assertions.append(
                {
                    "id": f"canonical-acceptable-{entry_idx}",
                    "text": f"Acceptable alternative '{entry['title']}' found.",
                    "passed": True,
                    "evidence": "Matched an acceptable alternative to a gold anchor.",
                }
            )

    # Forbidden decoys
    forbidden_present = False
    matched_forbidden: list[str] = []
    for entry in forbidden:
        for paper in papers:
            if _paper_matches_gold(paper, entry):
                forbidden_present = True
                matched_forbidden.append(entry["title"] or paper.get("title", ""))
                break

    assertions.append(
        {
            "id": "canonical-no-forbidden",
            "text": "No forbidden decoy papers are included.",
            "passed": not forbidden_present,
            "evidence": (
                "No forbidden decoys matched."
                if not forbidden_present
                else f"Matched forbidden decoys: {', '.join(matched_forbidden)}"
            ),
        }
    )

    must_score = (must_hits / max(len(must_find), 1)) * 20.0
    acceptable_score = (acceptable_hits / max(len(acceptable), 1)) * 5.0
    score = must_score + acceptable_score

    if forbidden_present:
        score = min(score, 8.0)

    return _clamp(score, 0.0, MAX_SCORES["canonical_quality"]), forbidden_present


def _score_justification_quality(
    papers: list[dict[str, Any]],
    full_papers: list[dict[str, Any]],
    assertions: list[dict[str, Any]],
) -> float:
    """
    Justification Quality score (0-20).

    Penalizes generic praise and very short or missing justifications.
    """
    if not full_papers:
        return 0.0

    total = 0.0
    for i, paper in enumerate(full_papers, start=1):
        text = (paper.get("irreplaceable") or "").strip()
        title = paper.get("title", f"Paper {i}")

        if not text:
            total += 0.0
            assertions.append(
                {
                    "id": f"justification-present-{i}",
                    "text": f"Paper {i} ('{title}') has a 'Why Irreplaceable' section.",
                    "passed": False,
                    "evidence": "Section is missing or empty.",
                }
            )
            continue

        lower = text.lower()
        generic_hits = [phrase for phrase in _GENERIC_PHRASES if phrase in lower]
        has_generic = bool(generic_hits)

        assertions.append(
            {
                "id": f"justification-generic-{i}",
                "text": f"Paper {i} ('{title}') avoids generic praise phrases.",
                "passed": not has_generic,
                "evidence": (
                    "No generic phrases detected."
                    if not has_generic
                    else f"Detected generic phrases: {', '.join(generic_hits)}"
                ),
            }
        )

        # Length heuristic.
        if has_generic:
            # Multiple generic phrases -> very low; single generic -> medium.
            if len(generic_hits) > 1:
                per_paper = 8.0
            else:
                per_paper = 12.0
        else:
            length = len(text)
            if length >= 150:
                per_paper = 20.0
            elif length >= 80:
                per_paper = 18.0
            elif length >= 40:
                per_paper = 14.0
            else:
                per_paper = 8.0

        total += per_paper

    return _clamp(total / len(full_papers), 0.0, MAX_SCORES["justification_quality"])


def _score_evidence_metadata(
    papers: list[dict[str, Any]], assertions: list[dict[str, Any]]
) -> float:
    """Evidence & Metadata score (0-10) based on per-paper field completeness."""
    if not papers:
        return 0.0

    required_fields = ("title", "authors", "year", "journal", "doi")
    total_fraction = 0.0

    for i, paper in enumerate(papers, start=1):
        present = 0
        for field in required_fields:
            value = paper.get(field)
            if field == "authors":
                if isinstance(value, list) and value:
                    present += 1
            elif field == "doi":
                # Count DOI as present only if it looks like a real DOI.
                normalized = _normalize_doi(str(value) if value else "")
                if normalized and re.match(r"^10\.\d{4,9}/.+$", normalized, re.I):
                    present += 1
            else:
                if value:
                    present += 1

        fraction = present / len(required_fields)
        total_fraction += fraction

        assertions.append(
            {
                "id": f"metadata-complete-{i}",
                "text": f"Paper {i} has complete metadata (title/authors/year/journal/DOI).",
                "passed": fraction >= 0.8,
                "evidence": f"{present}/{len(required_fields)} required fields present/valid.",
            }
        )

    average = total_fraction / len(papers)
    return _clamp(average * MAX_SCORES["evidence_metadata"], 0.0, MAX_SCORES["evidence_metadata"])


def _check_validation_sources(
    format_info: dict[str, Any], assertions: list[dict[str, Any]]
) -> bool:
    """Check that Selection Notes list a Validation Sources subsection."""
    if not format_info.get("has_selection_notes"):
        assertions.append(
            {
                "id": "format-validation-sources",
                "text": "Selection Notes contain a Validation Sources subsection with at least 3 sources.",
                "passed": False,
                "evidence": "Selection Notes section is missing.",
            }
        )
        return False

    notes_text = format_info.get("selection_notes_text", "")
    has_heading = bool(
        re.search(
            r"^#{0,3}\s*(?:[-*•]\s*)?\*?\*?Validation Sources",
            notes_text,
            re.MULTILINE | re.IGNORECASE,
        )
    )
    item_lines = [
        line
        for line in notes_text.splitlines()
        if re.match(r"^\s*(?:[-*•]|\d+\.)\s+\S", line)
    ]
    count = len(item_lines)
    passed = has_heading and count >= 3
    assertions.append(
        {
            "id": "format-validation-sources",
            "text": "Selection Notes contain a Validation Sources subsection with at least 3 sources.",
            "passed": passed,
            "evidence": (
                f"Validation Sources heading present: {has_heading}; "
                f"enumerated sources: {count}."
            ),
        }
    )
    return passed


def _check_alternative_candidates_quality(
    format_info: dict[str, Any], assertions: list[dict[str, Any]]
) -> bool:
    """Check that Alternative Candidates table has >=3 rows with specific reasons."""
    if not format_info.get("has_alternative_candidates"):
        assertions.append(
            {
                "id": "format-alternative-candidates-quality",
                "text": "Alternative Candidates section has at least 3 rows with specific rejection reasons.",
                "passed": False,
                "evidence": "Alternative Candidates section is missing.",
            }
        )
        return False

    text = format_info.get("alternative_candidates_text", "")
    rows: list[list[str]] = []
    for line in text.splitlines():
        if "|" not in line:
            continue
        if re.match(r"^\s*\|?[-:\|\s]+\|?\s*$", line):
            continue
        cols = [c.strip().strip("*") for c in line.split("|")]
        if cols and cols[0] == "":
            cols = cols[1:]
        if cols and cols[-1] == "":
            cols = cols[:-1]
        if len(cols) < 2 or not cols[0] or not cols[1]:
            continue
        first = cols[0].lower()
        if first in ("paper", "论文", "备选论文", "alternative", "candidate"):
            continue
        rows.append(cols)

    reasons = [cols[1] for cols in rows]
    count_ok = len(rows) >= 3

    generic_phrases = (
        "overlapping contribution",
        "similar contribution",
        "too similar",
        "duplicate",
        "not as influential",
        "not as important",
        "already covered",
        "redundant",
        "overlap",
    )
    generic_count = sum(
        1
        for r in reasons
        if any(p in r.lower() for p in generic_phrases) or len(r) < 15
    )
    specific_ok = generic_count < max(len(reasons), 1) / 2

    passed = count_ok and specific_ok
    assertions.append(
        {
            "id": "format-alternative-candidates-quality",
            "text": "Alternative Candidates section has at least 3 rows with specific rejection reasons.",
            "passed": passed,
            "evidence": (
                f"Candidate rows with reasons: {len(rows)}; "
                f"generic/short reasons: {generic_count}/{len(reasons)}."
            ),
        }
    )
    return passed


def _check_bibtex_quality(
    bib_path: Path | None, format_info: dict[str, Any], assertions: list[dict[str, Any]]
) -> bool:
    """Soft check for high-quality BibTeX (canonical keys, complete fields)."""
    if not format_info.get("bibtex_valid") or bib_path is None or not bib_path.exists():
        assertions.append(
            {
                "id": "format-bibtex-quality",
                "text": "BibTeX entries use canonical keys and complete core fields (indicates bundled-script usage).",
                "passed": False,
                "evidence": "BibTeX missing or not parseable.",
            }
        )
        return False

    text = bib_path.read_text(encoding="utf-8")
    starts = [m.start() for m in re.finditer(r"@\w+\s*\{", text)]
    if not starts:
        assertions.append(
            {
                "id": "format-bibtex-quality",
                "text": "BibTeX entries use canonical keys and complete core fields (indicates bundled-script usage).",
                "passed": False,
                "evidence": "No BibTeX entries found.",
            }
        )
        return False

    high_quality = True
    total = 0
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(text)
        block = text[start:end]
        total += 1
        key_match = re.search(r"@\w+\s*\{([^,]+),", block)
        key = key_match.group(1).strip() if key_match else ""
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*\d{4}[a-z]?$", key):
            high_quality = False
        fields = set(re.findall(r"\b(title|author|year|journal|doi)\s*=", block, re.I))
        if len(fields) < 4:
            high_quality = False

    passed = high_quality and total > 0
    assertions.append(
        {
            "id": "format-bibtex-quality",
            "text": "BibTeX entries use canonical keys and complete core fields (indicates bundled-script usage).",
            "passed": passed,
            "evidence": f"{total} BibTeX entries examined; high quality: {passed}.",
        }
    )
    return passed


def _score_output_format(
    format_info: dict[str, Any],
    expected_language: str,
    expected_n: int | None,
    assertions: list[dict[str, Any]],
    bib_path: Path | None = None,
) -> float:
    """Output Format score (0-10)."""
    score = MAX_SCORES["output_format"]

    # Language match.
    detected = format_info.get("detected_language", "unknown")
    language_ok = detected == expected_language or detected == "unknown"
    assertions.append(
        {
            "id": "format-language",
            "text": f"Output language matches expected language '{expected_language}'.",
            "passed": language_ok,
            "evidence": f"Detected language: {detected}; expected: {expected_language}.",
        }
    )
    if not language_ok:
        score -= 3.0

    # Required sections.
    checks = [
        ("format-selection-notes", "has_selection_notes", "Selection Notes section missing"),
        ("format-journal-distribution", "has_journal_distribution", "Journal Distribution table missing"),
        ("format-alternative-candidates", "has_alternative_candidates", "Alternative Candidates table missing"),
    ]
    for assert_id, key, message in checks:
        passed = bool(format_info.get(key))
        assertions.append(
            {
                "id": assert_id,
                "text": message.replace("missing", "present"),
                "passed": passed,
                "evidence": "Found in output." if passed else message + ".",
            }
        )
        if not passed:
            score -= 1.0

    # BibTeX validity.
    bibtex_valid = format_info.get("bibtex_valid", False)
    assertions.append(
        {
            "id": "format-bibtex-valid",
            "text": "BibTeX file is present and parseable.",
            "passed": bibtex_valid,
            "evidence": (
                "BibTeX parsed successfully."
                if bibtex_valid
                else "BibTeX missing, empty, or unparseable."
            ),
        }
    )
    if not bibtex_valid:
        score -= 3.0

    # Paper count vs expected_n.
    paper_count = format_info.get("paper_count", 0)
    if expected_n is not None and expected_n > 0:
        count_ok = paper_count == expected_n
        assertions.append(
            {
                "id": "format-paper-count",
                "text": f"Paper count matches expected_n={expected_n}.",
                "passed": count_ok,
                "evidence": f"Detected {paper_count} papers; expected {expected_n}.",
            }
        )
        if not count_ok:
            diff = abs(paper_count - expected_n)
            score -= 2.0 if diff > 1 else 1.0

    # BibTeX entry count vs detected paper count.
    bibtex_entries = format_info.get("bibtex_entries", 0)
    if paper_count > 0 and bibtex_valid:
        bib_count_ok = bibtex_entries == paper_count
        assertions.append(
            {
                "id": "format-bibtex-count",
                "text": "BibTeX entry count matches detected paper count.",
                "passed": bib_count_ok,
                "evidence": f"{bibtex_entries} BibTeX entries vs {paper_count} papers.",
            }
        )
        if not bib_count_ok:
            score -= 3.0

    # New skill-quality checks.
    if not _check_validation_sources(format_info, assertions):
        score -= 1.0
    if not _check_alternative_candidates_quality(format_info, assertions):
        score -= 1.0

    # Soft, non-penalizing bundled-script / BibTeX quality assertion.
    _check_bibtex_quality(bib_path, format_info, assertions)

    return _clamp(score, 0.0, MAX_SCORES["output_format"])


def _score_interaction(
    format_info: dict[str, Any],
    constraints: dict[str, Any],
    expected_language: str,
    assertions: list[dict[str, Any]],
) -> float:
    """Interaction score (0-15) based on PDF / Chinese literature questions."""
    score = MAX_SCORES["interaction"]

    pdf_setting = constraints.get("pdf_download", "default")
    asks_pdf = format_info.get("asks_pdf_download", False)

    if pdf_setting == "ask":
        passed = asks_pdf
        assertions.append(
            {
                "id": "interaction-pdf-ask",
                "text": "Output asks about PDF download because task constraint is 'ask'.",
                "passed": passed,
                "evidence": f"ask_pdf_download={asks_pdf}.",
            }
        )
        if not passed:
            score -= 7.5
    elif pdf_setting == "skip_explicit":
        passed = not asks_pdf
        assertions.append(
            {
                "id": "interaction-pdf-skip",
                "text": "Output does not ask about PDF download because task constraint is 'skip_explicit'.",
                "passed": passed,
                "evidence": f"ask_pdf_download={asks_pdf}.",
            }
        )
        if not passed:
            score -= 7.5
    else:
        assertions.append(
            {
                "id": "interaction-pdf-default",
                "text": "PDF download constraint is 'default'; no hard interaction requirement enforced.",
                "passed": True,
                "evidence": f"ask_pdf_download={asks_pdf}.",
            }
        )

    chinese_question_required = bool(constraints.get("chinese_literature_question", False))
    asks_chinese = format_info.get("asks_chinese_literature", False)

    if expected_language == "zh" and chinese_question_required:
        passed = asks_chinese
        assertions.append(
            {
                "id": "interaction-chinese-literature",
                "text": "Output asks about Chinese literature inclusion for a Chinese prompt.",
                "passed": passed,
                "evidence": f"ask_chinese_literature={asks_chinese}.",
            }
        )
        if not passed:
            score -= 7.5
    else:
        assertions.append(
            {
                "id": "interaction-chinese-literature",
                "text": "Chinese literature question not required by task constraints.",
                "passed": True,
                "evidence": (
                    f"expected_language={expected_language}, "
                    f"chinese_literature_question={chinese_question_required}."
                ),
            }
        )

    return _clamp(score, 0.0, MAX_SCORES["interaction"])


# ---------------------------------------------------------------------------
# Critical caps
# ---------------------------------------------------------------------------


def _is_refusal_output(text: str, paper_count: int) -> bool:
    """Detect whether a model output is a polite refusal / conceptual answer."""
    if paper_count > 0:
        return False
    lower = text.lower()
    refusal_signals = (
        "outside the scope",
        "not a reading list",
        "conceptual overview",
        "i can help",
        "i'm not sure",
        "not how",
        "different request",
        "not appropriate",
        "超出了范围",
        "不是文献列表",
        "不是论文",
        "我可以帮你",
    )
    return any(signal in lower for signal in refusal_signals)


def _compute_critical_caps(
    format_info: dict[str, Any],
    task: dict[str, Any],
    forbidden_present: bool,
    papers: list[dict[str, Any]],
    bib_path: Path | None,
    is_boundary_refusal: bool = False,
) -> list[dict[str, Any]]:
    """Build the critical_caps list and return it."""
    caps: list[dict[str, Any]] = []
    constraints = task.get("constraints", {})
    expected_language = task.get("expected_output_language", "en")

    # 1. Forbidden decoy included.
    caps.append(
        {
            "id": "cap-forbidden-decoy",
            "description": "Includes a forbidden decoy paper",
            "triggered": forbidden_present,
            "cap": 60,
            "evidence": (
                "At least one forbidden decoy was matched."
                if forbidden_present
                else "No forbidden decoys matched."
            ),
        }
    )

    # 2. Wrong output language (not applicable to boundary refusals).
    detected = format_info.get("detected_language", "unknown")
    language_mismatch = (
        not is_boundary_refusal
        and detected != expected_language
        and detected != "unknown"
    )
    caps.append(
        {
            "id": "cap-wrong-language",
            "description": "Wrong output language",
            "triggered": language_mismatch,
            "cap": 70,
            "evidence": f"Detected '{detected}', expected '{expected_language}'." + (
                " Boundary refusal; language cap waived." if is_boundary_refusal else ""
            ),
        }
    )

    # 3. Missing or malformed BibTeX (not applicable to boundary refusals).
    bibtex_valid = format_info.get("bibtex_valid", False)
    bib_missing = bib_path is None or not bib_path.exists() if bib_path else True
    paper_count = format_info.get("paper_count", 0)
    bibtex_entries = format_info.get("bibtex_entries", 0)
    bib_count_bad = bool(paper_count and bibtex_valid and bibtex_entries != paper_count)
    bibtex_bad = (
        not is_boundary_refusal
        and (bib_missing or not bibtex_valid or bib_count_bad)
    )
    caps.append(
        {
            "id": "cap-bibtex",
            "description": "Missing or malformed BibTeX",
            "triggered": bibtex_bad,
            "cap": 70,
            "evidence": (
                "BibTeX file missing, unparseable, or entry count does not match paper count."
                if bibtex_bad
                else "BibTeX parsed successfully with matching entry count or boundary refusal."
            ),
        }
    )

    # 4. Does not ask about PDF download.
    pdf_setting = constraints.get("pdf_download", "default")
    asks_pdf = format_info.get("asks_pdf_download", False)
    no_pdf_ask = pdf_setting == "ask" and not asks_pdf
    caps.append(
        {
            "id": "cap-no-pdf-question",
            "description": "Does not ask about PDF download",
            "triggered": no_pdf_ask,
            "cap": 85,
            "evidence": f"pdf_download='{pdf_setting}', asks_pdf_download={asks_pdf}.",
        }
    )

    # 5. Chinese prompt: no Chinese-literature question.
    chinese_required = bool(constraints.get("chinese_literature_question", False))
    asks_chinese = format_info.get("asks_chinese_literature", False)
    no_chinese_question = expected_language == "zh" and chinese_required and not asks_chinese
    caps.append(
        {
            "id": "cap-no-chinese-question",
            "description": "Chinese prompt: no Chinese-literature question",
            "triggered": no_chinese_question,
            "cap": 85,
            "evidence": (
                f"expected_language='{expected_language}', "
                f"chinese_literature_question={chinese_required}, "
                f"asks_chinese_literature={asks_chinese}."
            ),
        }
    )

    # 6. Fabricated evidence (placeholder / clearly invalid metadata).
    fabricated = False
    fabricated_evidence: list[str] = []
    doi_pattern = re.compile(r"^10\.\d{4,9}/.+$")
    for i, paper in enumerate(papers, start=1):
        title = (paper.get("title") or "").strip()
        authors = paper.get("authors", [])
        journal = (paper.get("journal") or "").strip()
        doi_raw = (paper.get("doi") or "").strip()
        doi = _normalize_doi(doi_raw)
        year = (paper.get("year") or "").strip()

        for value, field in ((title, "title"), (journal, "journal"), (year, "year")):
            if value and value.lower() in _PLACEHOLDER_VALUES:
                fabricated = True
                fabricated_evidence.append(f"Paper {i} {field}='{value}'")
        if doi_raw and not doi_pattern.match(doi):
            fabricated = True
            fabricated_evidence.append(f"Paper {i} DOI='{doi_raw}' does not look like a DOI")
        if authors:
            for author in authors:
                if author.strip().lower() in _PLACEHOLDER_VALUES:
                    fabricated = True
                    fabricated_evidence.append(f"Paper {i} author='{author}'")

    caps.append(
        {
            "id": "cap-fabricated-evidence",
            "description": "Fabricated or placeholder metadata",
            "triggered": fabricated,
            "cap": 40,
            "evidence": (
                "; ".join(fabricated_evidence)
                if fabricated
                else "No obvious placeholder or invalid DOI metadata detected."
            ),
        }
    )

    return caps


# ---------------------------------------------------------------------------
# Main grading pipeline
# ---------------------------------------------------------------------------


def grade_output(
    task_path: str | Path,
    output_path: str | Path,
    gold_path: str | Path | None,
    configuration: str,
    bib_path: str | Path | None = None,
) -> dict[str, Any]:
    """
    Grade a single output and return the grading result dict.

    Parameters
    ----------
    task_path : str or Path
        Path to the public task JSON.
    output_path : str or Path
        Path to the model's Markdown output.
    gold_path : str or Path or None
        Path to the private gold JSON. Optional.
    configuration : str
        Either ``"with_skill"`` or ``"without_skill"``.
    bib_path : str or Path or None
        Optional explicit BibTeX path. If omitted, inferred from ``output_path``.
    """
    task_path = Path(task_path)
    output_path = Path(output_path)
    if gold_path is not None:
        gold_path = Path(gold_path)
    if bib_path is not None:
        bib_path = Path(bib_path)

    task = _load_json(task_path) or {}
    task_id = task.get("id", output_path.stem)
    expected_language = task.get("expected_output_language", "en")
    expected_n = task.get("expected_n")
    constraints = task.get("constraints", {})

    gold = _load_json(gold_path)
    gold_task = _get_task_entry(gold, task_id) if gold else None

    # Run the format checker.
    format_info = check_format(output_path, bib_path)
    full_papers = format_info.get("papers", [])

    md_text = output_path.read_text(encoding="utf-8")
    is_boundary = task.get("domain_type") == "boundary"
    is_refusal = is_boundary and _is_refusal_output(md_text, format_info.get("paper_count", 0))

    # Boundary refusal: model correctly declined to curate a reading list.
    if is_refusal:
        result = {
            "task_id": task_id,
            "configuration": configuration,
            "scores": {
                "coverage": 0.0,
                "canonical_quality": 0.0,
                "justification_quality": 0.0,
                "evidence_metadata": 0.0,
                "output_format": 0.0,
                "interaction": 0.0,
            },
            "assertions": [
                {
                    "id": "boundary-refusal",
                    "text": "Model correctly declined to produce a reading list for a boundary/near-miss request.",
                    "passed": True,
                    "evidence": "No papers detected and output contains refusal/overview language.",
                }
            ],
            "critical_caps": [],
            "raw_score": 0.0,
            "capped_score": 100.0,
            "total_score": 100.0,
        }
        return result

    # Boundary over-trigger: model produced a reading list when it should not have.
    if is_boundary and format_info.get("paper_count", 0) > 0:
        assertions: list[dict[str, Any]] = [
            {
                "id": "boundary-overtrigger",
                "text": "Model produced a reading list for a boundary/near-miss request.",
                "passed": False,
                "evidence": f"Detected {format_info.get('paper_count', 0)} papers in a task that should not trigger curation.",
            }
        ]
        result = {
            "task_id": task_id,
            "configuration": configuration,
            "scores": {
                "coverage": 0.0,
                "canonical_quality": 0.0,
                "justification_quality": 0.0,
                "evidence_metadata": 0.0,
                "output_format": 0.0,
                "interaction": 0.0,
            },
            "assertions": assertions,
            "critical_caps": [
                {
                    "id": "cap-overtrigger",
                    "description": "Produced a reading list for a near-miss/boundary request",
                    "triggered": True,
                    "cap": 0,
                    "evidence": "Boundary task should not produce a curated reading list.",
                }
            ],
            "raw_score": 0.0,
            "capped_score": 0.0,
            "total_score": 0.0,
        }
        return result

    # The public paper dict does not include summary/irreplaceable text, so
    # re-extract the internal representation for justification scoring.
    try:
        from .format_checker import _split_into_paper_sections, _extract_paper_metadata
    except ImportError:  # pragma: no cover
        from format_checker import _split_into_paper_sections, _extract_paper_metadata

    sections = _split_into_paper_sections(md_text)
    internal_papers = [
        _extract_paper_metadata(title, body) for title, body in sections
    ]

    assertions = []

    # ----- Six dimensions -----
    coverage_score = _score_coverage(
        full_papers, constraints.get("must_cover_branches", []), assertions
    )
    canonical_score, forbidden_present = _score_canonical_quality(
        full_papers, gold_task, assertions
    )
    justification_score = _score_justification_quality(
        full_papers, internal_papers, assertions
    )
    metadata_score = _score_evidence_metadata(full_papers, assertions)
    inferred_bib = bib_path or output_path.with_suffix(".bib")
    format_score = _score_output_format(
        format_info, expected_language, expected_n, assertions, bib_path=inferred_bib
    )
    interaction_score = _score_interaction(
        format_info, constraints, expected_language, assertions
    )

    scores = {
        "coverage": round(coverage_score, 2),
        "canonical_quality": round(canonical_score, 2),
        "justification_quality": round(justification_score, 2),
        "evidence_metadata": round(metadata_score, 2),
        "output_format": round(format_score, 2),
        "interaction": round(interaction_score, 2),
    }

    raw_score = round(sum(scores.values()), 2)

    # ----- Critical caps -----
    critical_caps = _compute_critical_caps(
        format_info, task, forbidden_present, full_papers, inferred_bib,
        is_boundary_refusal=is_refusal
    )

    triggered_caps = [c for c in critical_caps if c.get("triggered")]
    if triggered_caps:
        lowest_cap = min(c["cap"] for c in triggered_caps)
    else:
        lowest_cap = 100.0
    capped_score = min(raw_score, lowest_cap)

    result = {
        "task_id": task_id,
        "configuration": configuration,
        "scores": scores,
        "assertions": assertions,
        "critical_caps": critical_caps,
        "raw_score": raw_score,
        "capped_score": round(capped_score, 2),
        "total_score": round(capped_score, 2),
    }
    return result


def _write_grading(result: dict[str, Any], output_path: Path) -> Path:
    """Write ``grading.json`` next to the output Markdown file."""
    grading_path = output_path.parent / "grading.json"
    grading_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return grading_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Grade a single econ-compass benchmark output."
    )
    parser.add_argument("--task", required=True, help="Path to the task JSON file")
    parser.add_argument("--output", required=True, help="Path to the Markdown output")
    parser.add_argument("--gold", help="Path to the private gold JSON file")
    parser.add_argument(
        "--config",
        required=True,
        choices=["with_skill", "without_skill"],
        help="Configuration being evaluated",
    )
    parser.add_argument("--bib", help="Optional explicit path to the BibTeX file")
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Also print the grading result to stdout",
    )
    args = parser.parse_args()

    result = grade_output(
        task_path=args.task,
        output_path=args.output,
        gold_path=args.gold,
        configuration=args.config,
        bib_path=args.bib,
    )

    grading_path = _write_grading(result, Path(args.output))
    if args.stdout:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"Grading written to {grading_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
