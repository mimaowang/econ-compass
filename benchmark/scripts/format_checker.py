#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
format_checker.py

Programmatic format checker for an econ-compass reading-list output.

Inputs
------
* Markdown output file (required).
* Optional BibTeX file.

Outputs
-------
A JSON object with:
    paper_count, papers, has_selection_notes, has_journal_distribution,
    has_alternative_candidates, bibtex_valid, bibtex_entries,
    detected_language, asks_pdf_download, asks_chinese_literature, errors

The checker uses only the Python standard library plus an optional
``bibtexparser`` import for BibTeX validation.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------


def _read_text(path: Path) -> str:
    """Read a text file with UTF-8 encoding, return empty string on error."""
    try:
        return path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    except Exception as exc:  # pragma: no cover
        return ""


def _normalize_whitespace(text: str) -> str:
    """Collapse repeated whitespace/newlines into a single space."""
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------------------
# Markdown paper extraction
# ---------------------------------------------------------------------------

# Matches headings such as:
#   ## Paper 1: Title
#   ## Paper 1. Title
#   ## 论文 1：标题
#   ## Paper #1: Title
_PAPER_HEADER_RE = re.compile(
    r"^##\s+(?:Paper|论文)\s*#?\s*\d+[:.:\s\-–—]+\s*(.+)$",
    re.MULTILINE | re.IGNORECASE,
)

# Section headings for Summary / Why Irreplaceable (English and Chinese aware).
_SUMMARY_HEADINGS = (
    "### Summary",
    "## Summary",
    "### 摘要",
    "## 摘要",
    "### 总结",
)
_IRREPLACEABLE_HEADINGS = (
    "### Why This Paper Is Irreplaceable",
    "## Why This Paper Is Irreplaceable",
    "### Why This Paper is Irreplaceable",
    "### Why This Is Irreplaceable",
    "### Why It Is Irreplaceable",
    "### Why Irreplaceable",
    "## Why Irreplaceable",
    "### 不可替代性",
    "### 为什么不可替代",
    "### 本文为何不可替代",
)

# Simple patterns to grab bullet metadata lines.
# Handles forms such as:
#   - **Authors**: Becker, Gary S.
#   * Authors: Becker, Gary S.
#   Authors：贝克
_BULLET_PREFIX = r"^\s*(?:[-*•]\s*)?\*?\*?\s*"
# Allows an optional closing bold marker before the colon (e.g. **Authors** :).
_BOLD_BEFORE_COLON = r"\s*\*?\*?\s*[:：][^\S\n]*"

_AUTHORS_RE = re.compile(_BULLET_PREFIX + r"Authors" + _BOLD_BEFORE_COLON + r"(.+)$", re.I | re.M)
_AUTHORS_RE_ZH = re.compile(_BULLET_PREFIX + r"作者" + _BOLD_BEFORE_COLON + r"(.+)$", re.I | re.M)
_YEAR_RE = re.compile(_BULLET_PREFIX + r"Year" + _BOLD_BEFORE_COLON + r"(\d{4})$", re.I | re.M)
_YEAR_RE_ZH = re.compile(_BULLET_PREFIX + r"年份" + _BOLD_BEFORE_COLON + r"(\d{4})$", re.I | re.M)
_JOURNAL_RE = re.compile(_BULLET_PREFIX + r"Journal" + _BOLD_BEFORE_COLON + r"(.+)$", re.I | re.M)
_JOURNAL_RE_ZH = re.compile(_BULLET_PREFIX + r"期刊" + _BOLD_BEFORE_COLON + r"(.+)$", re.I | re.M)
_DOI_RE = re.compile(_BULLET_PREFIX + r"DOI" + _BOLD_BEFORE_COLON + r"(.+)$", re.I | re.M)
_BRANCH_RE = re.compile(
    _BULLET_PREFIX + r"(?:Core\s+)?Branch(?:/Cluster)?" + _BOLD_BEFORE_COLON + r"(.+)$", re.I | re.M
)
_BRANCH_RE_ZH = re.compile(
    _BULLET_PREFIX + r"(?:核心)?(?:分支|聚类|领域)" + _BOLD_BEFORE_COLON + r"(.+)$", re.I | re.M
)


def _split_into_paper_sections(text: str) -> list[tuple[str, str]]:
    """
    Split the Markdown text into (title, body) sections, one per paper.

    The function is intentionally tolerant of minor formatting variations.
    """
    matches = list(_PAPER_HEADER_RE.finditer(text))
    if not matches:
        return []

    sections: list[tuple[str, str]] = []
    for i, match in enumerate(matches):
        title = _normalize_whitespace(match.group(1))
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end]
        sections.append((title, body))
    return sections


def _extract_section(
    body: str,
    headings: tuple[str, ...],
    normalize: bool = True,
    include_subsections: bool = False,
) -> str:
    """Extract text following one of the given headings until the next heading."""
    lines = body.splitlines()
    collecting = False
    collected: list[str] = []
    matched_level: int | None = None

    for line in lines:
        stripped = line.strip()

        # Stop at horizontal rules.
        if collecting and (
            re.match(r"^-{3,}\s*$", stripped)
            or re.match(r"^\*\*\*\s*$", stripped)
        ):
            break

        # Stop at a heading.  When including subsections, only stop at a heading
        # of the same or higher level than the matched heading.
        if collecting and stripped.startswith("#"):
            level_match = re.match(r"^(#{1,6})\s+", stripped)
            level = len(level_match.group(1)) if level_match else 6
            if not include_subsections or matched_level is None or level <= matched_level:
                break

        # Start collection when we hit the target heading.
        if not collecting:
            line_heading_text = re.sub(r"^#+\s*", "", stripped).lower()
            for heading in headings:
                target = heading.lstrip("#").strip().lower()
                if line_heading_text.startswith(target):
                    collecting = True
                    level_match = re.match(r"^(#{1,6})\s+", stripped)
                    matched_level = len(level_match.group(1)) if level_match else 2
                    break
            continue

        collected.append(line)

    result = "\n".join(collected)
    if normalize:
        result = _normalize_whitespace(result)
    return result


def _first_match(patterns: list[re.Pattern], text: str) -> str:
    """Return the first non-empty match from a list of regex patterns."""
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            value = match.group(1).strip()
            if value:
                return value
    return ""


def _split_authors(author_text: str) -> list[str]:
    """Split an author string on common delimiters (; , and)."""
    if not author_text:
        return []
    # Use semicolon first, otherwise comma if it looks like a list.
    if ";" in author_text:
        parts = author_text.split(";")
    elif "," in author_text and len(author_text.split(",")) > 2:
        parts = author_text.split(",")
    else:
        parts = [author_text]
    return [_normalize_whitespace(p) for p in parts if _normalize_whitespace(p)]


def _extract_paper_metadata(title: str, body: str) -> dict[str, Any]:
    """Extract per-paper metadata from a paper section body."""
    authors_text = _first_match([_AUTHORS_RE, _AUTHORS_RE_ZH], body)
    authors = _split_authors(authors_text)

    year = _first_match([_YEAR_RE, _YEAR_RE_ZH], body)
    journal = _first_match([_JOURNAL_RE, _JOURNAL_RE_ZH], body)
    doi = _first_match([_DOI_RE], body)
    core_branch = _first_match([_BRANCH_RE, _BRANCH_RE_ZH], body)

    summary = _extract_section(body, _SUMMARY_HEADINGS)
    irreplaceable = _extract_section(body, _IRREPLACEABLE_HEADINGS)

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "journal": journal,
        "doi": doi,
        "has_summary": bool(summary),
        "has_irreplaceable": bool(irreplaceable),
        "core_branch": core_branch,
        "summary": summary,
        "irreplaceable": irreplaceable,
    }


# ---------------------------------------------------------------------------
# Auxiliary section detection
# ---------------------------------------------------------------------------

_SELECTION_NOTES_HEADINGS = (
    "## Selection Notes",
    "## 选文说明",
    "## 选择说明",
)
_JOURNAL_DISTRIBUTION_HEADINGS = (
    "**Journal Distribution:**",
    "### Journal Distribution",
    "## Journal Distribution",
    "**期刊分布：**",
    "### 期刊分布",
)
_ALTERNATIVE_CANDIDATES_HEADINGS = (
    "**Alternative Candidates Considered and Rejected:**",
    "### Alternative Candidates Considered",
    "## Alternative Candidates Considered",
    "**备选文献：**",
    "### 备选文献",
)
_VALIDATION_SOURCES_HEADINGS = (
    "### Validation Sources",
    "## Validation Sources",
    "**Validation Sources:**",
    "### 验证来源",
    "## 验证来源",
)


def _has_section(text: str, headings: tuple[str, ...]) -> bool:
    """Check whether a Markdown section with any of the given headings exists."""
    for heading in headings:
        # Match the heading text regardless of surrounding markdown markers.
        # Supports leading ## headers, bullets, bold wrappers (** or __), etc.
        escaped = re.escape(heading.lstrip("#*-_").strip())
        pattern = re.compile(
            r"^\s*#{0,3}\s*(?:[-*•]\s*)?\*?\*?_?_?" + escaped,
            re.MULTILINE | re.IGNORECASE,
        )
        if pattern.search(text):
            return True
    return False


def _has_table_with_header(text: str, header_keywords: tuple[str, ...]) -> bool:
    """Return True if a markdown table with one of the header keywords exists."""
    # A markdown table header line contains at least one pipe.
    for line in text.splitlines():
        if "|" in line:
            lower = line.lower()
            if any(keyword.lower() in lower for keyword in header_keywords):
                # Ensure it is not just the separator line.
                if not re.match(r"^\s*\|?[-:\|\s]+\|?\s*$", line):
                    return True
    return False


def _detect_selection_notes(text: str) -> bool:
    return _has_section(text, _SELECTION_NOTES_HEADINGS)


def _detect_journal_distribution(text: str) -> bool:
    if not _has_section(text, _JOURNAL_DISTRIBUTION_HEADINGS):
        return False
    return _has_table_with_header(text, ("Journal", "期刊", "Count", "数量"))


def _detect_alternative_candidates(text: str) -> bool:
    if not _has_section(text, _ALTERNATIVE_CANDIDATES_HEADINGS):
        return False
    return _has_table_with_header(text, ("Paper", "Why Rejected", "Replaced By", "论文", "备选"))


def _extract_selection_notes_text(text: str) -> str:
    """Return the raw text of the Selection Notes section, if present."""
    return _extract_section(
        text, _SELECTION_NOTES_HEADINGS, normalize=False, include_subsections=True
    )


def _extract_alternative_candidates_text(text: str) -> str:
    """Return the raw text of the Alternative Candidates section, if present."""
    return _extract_section(
        text, _ALTERNATIVE_CANDIDATES_HEADINGS, normalize=False, include_subsections=True
    )


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------

# CJK Unified Ideographs (common Chinese characters).
# NOTE: Python regex does not support \u for code points above U+FFFF;
# using only the Basic CJK block is sufficient for en/zh discrimination.
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def _detect_language(text: str) -> str:
    """
    Detect whether the text is mostly English, Chinese, or unknown.

    The heuristic counts CJK ideographs vs. alphabetic characters.
    """
    if not text:
        return "unknown"

    cjk_count = len(_CJK_RE.findall(text))
    alpha_count = len(re.findall(r"[a-zA-Z]", text))
    total = cjk_count + alpha_count
    if total == 0:
        return "unknown"

    cjk_ratio = cjk_count / total
    if cjk_ratio > 0.20:
        return "zh"
    if cjk_ratio < 0.05:
        return "en"
    return "unknown"


# ---------------------------------------------------------------------------
# Interaction question detection
# ---------------------------------------------------------------------------

_PDF_QUESTION_PATTERNS = (
    # English proactive offers
    r"would\s+you\s+like\s+(?:me\s+to\s+)?(?:download|fetch|get)\s+(?:the\s+)?pdfs?",
    r"do\s+you\s+want\s+(?:me\s+to\s+)?(?:download|fetch|get)\s+(?:the\s+)?pdfs?",
    r"shall\s+i\s+(?:download|fetch|get)\s+(?:the\s+)?pdfs?",
    r"should\s+i\s+(?:download|fetch|get)\s+(?:the\s+)?pdfs?",
    r"(?:download|fetch|get)\s+(?:the\s+)?pdfs?\s+(?:for\s+you|now\s?\?)",
    r"i\s+can\s+(?:download|fetch|get)\s+(?:the\s+)?pdfs?",
    # Chinese proactive offers
    r"是否(?:需要|要|希望).*?(?:下载|获取).*?pdf",
    r"需要我.*?下载.*?pdf",
    r"想(?:要|让)我.*?下载.*?pdf",
    r"pdf.*?下载",
)

_CHINESE_LITERATURE_PATTERNS = (
    r"中文文献",
    r"chinese\s+(?:literature|papers|sources|references|articles)",
    r"是否(?:需要|要|希望).*?(?:中文|中国).*?(?:文献|论文)",
    r"需要.*?(?:中文|中国).*?(?:文献|论文)",
    r"(?:包含|纳入|包括).*?(?:中文|中国).*?(?:文献|论文)",
)


def _detect_asks_pdf_download(text: str) -> bool:
    lower = text.lower()
    # Exclude the passive "PDF Download Results" progress-report section.
    if "pdf download results" in lower or "pdf download" in lower:
        # If it only contains a report, still allow a proactive question elsewhere.
        pass
    for pattern in _PDF_QUESTION_PATTERNS:
        if re.search(pattern, lower):
            return True
    return False


def _detect_asks_chinese_literature(text: str) -> bool:
    lower = text.lower()
    for pattern in _CHINESE_LITERATURE_PATTERNS:
        if re.search(pattern, lower):
            return True
    return False


# ---------------------------------------------------------------------------
# BibTeX validation
# ---------------------------------------------------------------------------


def _parse_bibtex(path: Path | None) -> tuple[bool, int, list[str]]:
    """
    Parse a BibTeX file and return (valid, entry_count, errors).

    If ``bibtexparser`` is installed it is used; otherwise a lightweight
    regex/brace-balance fallback is used.
    """
    if path is None or not path.exists():
        return False, 0, ["BibTeX file missing or not provided"]

    text = _read_text(path)
    if not text.strip():
        return False, 0, ["BibTeX file is empty"]

    # Prefer bibtexparser when available.
    try:
        import bibtexparser  # type: ignore

        try:
            library = bibtexparser.loads(text)
            entries = getattr(library, "entries", library)
            # bibtexparser 1.x returns a BibDatabase with .entries
            if isinstance(entries, list):
                entry_count = len(entries)
            else:
                entry_count = len(entries.entries)
            if entry_count == 0:
                return False, 0, ["BibTeX parsed but contains no entries"]
            return True, entry_count, []
        except Exception as exc:
            return False, 0, [f"bibtexparser failed to parse BibTeX: {exc}"]
    except ImportError:
        pass

    # Fallback: count @<type>{ ... } blocks with balanced braces.
    entry_pattern = re.compile(r"@(\w+)\s*\{", re.MULTILINE)
    starts = [m.start() for m in entry_pattern.finditer(text)]
    if not starts:
        return False, 0, ["No BibTeX entries found with fallback parser"]

    valid_entries = 0
    errors: list[str] = []
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(text)
        block = text[start:end]
        brace_balance = 0
        opened = False
        for ch in block:
            if ch == "{":
                brace_balance += 1
                opened = True
            elif ch == "}":
                brace_balance -= 1
        if opened and brace_balance == 0:
            valid_entries += 1
        else:
            errors.append(f"BibTeX entry {i + 1} has unbalanced braces")

    if valid_entries == 0:
        return False, 0, errors or ["No valid BibTeX entries found"]
    return True, valid_entries, errors


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_papers(md_path: str | Path) -> list[dict[str, Any]]:
    """
    Extract paper metadata and textual sections from a Markdown file.

    Returns a list of dicts with full ``summary`` and ``irreplaceable`` text
    in addition to the public metadata fields.
    """
    text = _read_text(Path(md_path))
    sections = _split_into_paper_sections(text)
    return [_extract_paper_metadata(title, body) for title, body in sections]


def check_format(md_path: str | Path, bib_path: str | Path | None = None) -> dict[str, Any]:
    """
    Check the format of an econ-compass reading-list Markdown file.

    Parameters
    ----------
    md_path : str or Path
        Path to the Markdown output file.
    bib_path : str or Path, optional
        Path to the BibTeX file. If omitted, the function looks for a
        sibling ``.bib`` file with the same stem as ``md_path``.

    Returns
    -------
    dict
        Format-check result as described in the module docstring.
    """
    md_path = Path(md_path)
    if bib_path is None:
        bib_path = md_path.with_suffix(".bib")
    else:
        bib_path = Path(bib_path)
        if not bib_path.exists() and not bib_path.is_absolute():
            # Try relative to the Markdown file's directory.
            candidate = md_path.parent / bib_path
            if candidate.exists():
                bib_path = candidate

    errors: list[str] = []
    text = _read_text(md_path)
    if not text.strip():
        errors.append("Markdown file is empty")

    papers = extract_papers(md_path)
    paper_count = len(papers)
    if paper_count == 0:
        errors.append("No papers detected; expected '## Paper N: Title' headings")

    # Language detection uses all summaries + irreplaceable justifications.
    language_sample = " ".join(
        (p.get("summary") or "") + " " + (p.get("irreplaceable") or "")
        for p in papers
    )
    detected_language = _detect_language(language_sample)

    has_selection_notes = _detect_selection_notes(text)
    has_journal_distribution = _detect_journal_distribution(text)
    has_alternative_candidates = _detect_alternative_candidates(text)

    selection_notes_text = _extract_selection_notes_text(text)
    alternative_candidates_text = _extract_alternative_candidates_text(text)

    asks_pdf_download = _detect_asks_pdf_download(text)
    asks_chinese_literature = _detect_asks_chinese_literature(text)

    bibtex_valid, bibtex_entries, bib_errors = _parse_bibtex(bib_path)
    errors.extend(bib_errors)
    if bibtex_valid and paper_count > 0 and bibtex_entries != paper_count:
        errors.append(
            f"BibTeX entry count mismatch: {bibtex_entries} entries vs {paper_count} papers"
        )

    # Surface obvious per-paper metadata gaps as errors.
    for i, paper in enumerate(papers, start=1):
        missing = [
            field
            for field in ("title", "year", "journal", "doi")
            if not paper.get(field)
        ]
        if missing:
            errors.append(f"Paper {i} missing fields: {', '.join(missing)}")

    # Strip internal summary/irreplaceable text before returning; they are
    # represented by the boolean flags.
    public_papers = []
    for paper in papers:
        public_papers.append(
            {
                "title": paper["title"],
                "authors": paper["authors"],
                "year": paper["year"],
                "journal": paper["journal"],
                "doi": paper["doi"],
                "has_summary": paper["has_summary"],
                "has_irreplaceable": paper["has_irreplaceable"],
                "core_branch": paper["core_branch"],
            }
        )

    return {
        "paper_count": paper_count,
        "papers": public_papers,
        "has_selection_notes": has_selection_notes,
        "has_journal_distribution": has_journal_distribution,
        "has_alternative_candidates": has_alternative_candidates,
        "selection_notes_text": selection_notes_text,
        "alternative_candidates_text": alternative_candidates_text,
        "bibtex_valid": bibtex_valid,
        "bibtex_entries": bibtex_entries,
        "detected_language": detected_language,
        "asks_pdf_download": asks_pdf_download,
        "asks_chinese_literature": asks_chinese_literature,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check the format of an econ-compass reading-list output."
    )
    parser.add_argument("markdown", help="Path to the Markdown output file")
    parser.add_argument("bibtex", nargs="?", help="Optional path to the BibTeX file")
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Print formatted JSON with indentation",
    )
    args = parser.parse_args()

    result = check_format(args.markdown, args.bibtex)
    indent = 2 if args.pretty else None
    print(json.dumps(result, indent=indent, ensure_ascii=False))
    return 1 if result.get("errors") else 0


if __name__ == "__main__":
    sys.exit(main())
