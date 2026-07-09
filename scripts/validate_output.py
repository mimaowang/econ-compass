#!/usr/bin/env python3
"""
validate_output.py

Validate an econ-compass Markdown reading list against the output specification
in ``references/output-specification.md``.

The script returns exit code 0 on success and 1 on failure, printing a JSON
validation report to stdout.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


SPEC_PATH = Path(__file__).resolve().parents[1] / "references" / "output-specification.md"

# Optional import: bibtexparser. If missing, fall back to a simple regex check.
try:
    import bibtexparser  # type: ignore
    _HAS_BIBTEXPARSER = True
except Exception:  # pragma: no cover
    _HAS_BIBTEXPARSER = False

ZH_PAPER = "\u8bba\u6587"
ZH_AUTHORS = "\u4f5c\u8005"
ZH_YEAR = "\u5e74\u4efd"
ZH_JOURNAL = "\u671f\u520a"
ZH_SUMMARY = "\u6458\u8981"
ZH_SUMMARY_ALT = "\u603b\u7ed3"
ZH_WHY_1 = "\u4e3a\u4ec0\u4e48\u4e0d\u53ef\u66ff\u4ee3"
ZH_WHY_2 = "\u4e3a\u4f55\u4e0d\u53ef\u66ff\u4ee3"
ZH_WHY_3 = "\u4e0d\u53ef\u66ff\u4ee3\u6027"
COLON_CLASS = ":\\uff1a.\\s\\-\\u2013\\u2014"

_PAPER_HEADER_RE = re.compile(
    rf"^##\s+(?:Paper|{ZH_PAPER})\s*#?\s*\d+[{COLON_CLASS}]+\s*(.+)$",
    re.MULTILINE | re.IGNORECASE,
)
_PAPER_SPLIT_RE = re.compile(
    rf"(?=^##\s+(?:Paper|{ZH_PAPER})\s*#?\s*\d+[{COLON_CLASS}]+)",
    re.MULTILINE | re.IGNORECASE,
)
_BULLET_PREFIX = r"^\s*(?:[-*+]\s*)?\*?\*?\s*"
_BOLD_COLON = r"\s*\*?\*?\s*[:\uff1a]\s*"


def _extract_paper_blocks(md_text: str) -> List[str]:
    """Return the raw text blocks that look like paper sections."""
    paper_blocks: List[str] = []
    for part in _PAPER_SPLIT_RE.split(md_text):
        if _PAPER_HEADER_RE.search(part):
            paper_blocks.append(part.strip())
    return paper_blocks


def _parse_paper(block: str) -> Dict[str, Any]:
    """Extract metadata and section presence from a paper block."""
    paper: Dict[str, Any] = {
        "title": None,
        "authors": None,
        "year": None,
        "journal": None,
        "doi": None,
        "has_summary": False,
        "has_why_irreplaceable": False,
    }

    title_match = _PAPER_HEADER_RE.search(block)
    if title_match:
        paper["title"] = title_match.group(1).strip()

    def get_field(labels: str):
        pattern = _BULLET_PREFIX + rf"(?:{labels})" + _BOLD_COLON + r"(.+)$"
        m = re.search(pattern, block, re.IGNORECASE | re.MULTILINE)
        return m.group(1).strip() if m else None

    paper["authors"] = get_field("|".join(["Authors", ZH_AUTHORS]))
    paper["year"] = get_field("|".join(["Year", ZH_YEAR]))
    paper["journal"] = get_field("|".join(["Journal", ZH_JOURNAL]))
    paper["doi"] = get_field(r"DOI")

    paper["has_summary"] = bool(
        re.search(rf"^###\s+(?:Summary|{ZH_SUMMARY}|{ZH_SUMMARY_ALT})", block, re.IGNORECASE | re.MULTILINE)
    )
    paper["has_why_irreplaceable"] = bool(
        re.search(
            rf"^###\s+(?:Why\s+This\s+Paper\s+Is\s+Irreplaceable|Why\s+Irreplaceable|{ZH_WHY_1}|{ZH_WHY_2}|{ZH_WHY_3})",
            block,
            re.IGNORECASE | re.MULTILINE,
        )
    )

    return paper


def _extract_selection_notes(md_text: str) -> str:
    """Return the Selection Notes section, or an empty string."""
    match = re.search(
        r"^##\s+Selection\s+Notes\s*\n(.*?)\n##\s",
        md_text,
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    if match:
        return match.group(1).strip()
    # Fallback: Selection Notes is the last section.
    match = re.search(
        r"^##\s+Selection\s+Notes\s*\n(.*)$",
        md_text,
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def _check_selection_notes(notes: str) -> Dict[str, Any]:
    """Check that Selection Notes contains the required subsections."""
    text_lower = notes.lower()
    checks = {
        "has_covered_branches": "covered branches" in text_lower,
        "has_journal_distribution_table": bool(
            re.search(r"\*\*Journal Distribution:\*\*\s*\n\|?\s*Journal", notes, re.IGNORECASE)
        ),
        "has_validation_sources": "validation sources" in text_lower,
        "has_alternative_candidates_table": bool(
            re.search(
                r"\*\*Alternative Candidates Considered and Rejected:\*\*\s*\n\|?\s*Paper",
                notes,
                re.IGNORECASE,
            )
        ),
    }
    checks["valid"] = all(checks.values())
    return checks


def _detect_language(text: str) -> str:
    """Return 'zh' if a sizable fraction of characters are CJK, else 'en'."""
    if not text:
        return "en"
    cjk_chars = len(re.findall(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]", text))
    total_chars = len(re.sub(r"\s", "", text))
    if total_chars == 0:
        return "en"
    ratio = cjk_chars / total_chars
    return "zh" if ratio > 0.1 else "en"


def _find_bibtex_file(md_path: Path, md_text: str) -> Optional[Path]:
    """Locate the companion BibTeX file next to the Markdown input."""
    if md_path:
        candidate = md_path.with_suffix(".bib")
        if candidate.exists():
            return candidate
    # Try to infer from the Markdown heading domain name.
    title_match = re.search(r"^#\s+(.+?)\s+Economics", md_text, re.MULTILINE)
    if title_match and md_path:
        domain = title_match.group(1).strip().lower().replace(" ", "-")
        candidate = md_path.parent / f"{domain}-reading-list.bib"
        if candidate.exists():
            return candidate
    return None


def _check_bibtex(bib_path: Optional[Path]) -> Dict[str, Any]:
    """Check whether the BibTeX file exists and is parseable."""
    result: Dict[str, Any] = {
        "file": str(bib_path) if bib_path else None,
        "exists": bool(bib_path and bib_path.exists()),
        "parseable": False,
        "entry_count": 0,
        "error": None,
    }
    if not result["exists"]:
        result["error"] = "BibTeX file not found."
        return result

    text = bib_path.read_text(encoding="utf-8")  # type: ignore[union-attr]

    if _HAS_BIBTEXPARSER:
        try:
            library = bibtexparser.loads(text)
            result["parseable"] = True
            result["entry_count"] = len(library.entries)
        except Exception as exc:  # pragma: no cover
            result["error"] = f"bibtexparser failed: {exc}"
    else:
        # Fallback: count @article entries and ensure balanced braces.
        entries = re.findall(r"@article\s*{", text, flags=re.IGNORECASE)
        result["entry_count"] = len(entries)
        result["parseable"] = entries and text.count("{") == text.count("}")
        if not result["parseable"]:
            result["error"] = "Fallback BibTeX check failed (unbalanced braces or no entries)."

    return result


def validate(
    md_text: str,
    md_path: Optional[Path] = None,
    expected_n: Optional[int] = None,
    expected_language: Optional[str] = None,
) -> Dict[str, Any]:
    """Validate a reading list and return a structured report."""
    report: Dict[str, Any] = {
        "valid": True,
        "paper_count": 0,
        "expected_paper_count": expected_n,
        "papers": [],
        "selection_notes": {},
        "bibtex": {},
        "language": {},
        "errors": [],
    }

    blocks = _extract_paper_blocks(md_text)
    report["paper_count"] = len(blocks)

    if expected_n is not None and len(blocks) != expected_n:
        report["valid"] = False
        report["errors"].append(
            f"Expected {expected_n} papers, found {len(blocks)}."
        )

    for idx, block in enumerate(blocks, start=1):
        paper = _parse_paper(block)
        missing: List[str] = []
        for field in ("title", "authors", "year", "journal", "doi"):
            if not paper.get(field):
                missing.append(field)
        if not paper["has_summary"]:
            missing.append("Summary section")
        if not paper["has_why_irreplaceable"]:
            missing.append("Why This Paper Is Irreplaceable section")

        paper["valid"] = not missing
        paper["missing"] = missing
        report["papers"].append(paper)

        if missing:
            report["valid"] = False
            report["errors"].append(f"Paper {idx} missing: {', '.join(missing)}")

    notes = _extract_selection_notes(md_text)
    selection_checks = _check_selection_notes(notes)
    report["selection_notes"] = {
        "present": bool(notes),
        "checks": selection_checks,
    }
    if not selection_checks["valid"]:
        report["valid"] = False
        missing_notes = [k for k, v in selection_checks.items() if not v and k != "valid"]
        report["errors"].append(
            f"Selection Notes missing required elements: {', '.join(missing_notes)}"
        )

    bib_path = _find_bibtex_file(md_path, md_text)
    bib_report = _check_bibtex(bib_path)
    report["bibtex"] = bib_report
    if not bib_report.get("exists") or not bib_report.get("parseable"):
        report["valid"] = False
        report["errors"].append(
            f"BibTeX file issue: {bib_report.get('error', 'unknown')}"
        )
    elif len(blocks) > 0 and bib_report.get("entry_count") != len(blocks):
        report["valid"] = False
        report["errors"].append(
            f"BibTeX entry count mismatch: found {bib_report.get('entry_count')}, expected {len(blocks)}."
        )

    if expected_n is not None and bib_report.get("entry_count") not in (0, expected_n):
        report["valid"] = False
        report["errors"].append(
            f"Expected {expected_n} BibTeX entries, found {bib_report.get('entry_count')}."
        )

    # Language detection is performed on Summary + Why Irreplaceable blocks.
    lang_text = ""
    for block in blocks:
        sections = re.findall(
            r"^###\s+(?:Summary|Why\s+This\s+Paper\s+Is\s+Irreplaceable)\s*\n(.*?)(?=^###|\Z)",
            block,
            re.IGNORECASE | re.MULTILINE | re.DOTALL,
        )
        lang_text += "\n".join(sections)

    detected_language = _detect_language(lang_text)
    report["language"] = {
        "detected": detected_language,
        "expected": expected_language,
    }
    if expected_language and detected_language != expected_language:
        report["valid"] = False
        report["errors"].append(
            f"Expected language '{expected_language}', detected '{detected_language}'."
        )

    return report


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate an econ-compass Markdown reading list against the output specification."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/validate_output.py -i growth-reading-list.md\n"
            "  python scripts/validate_output.py -i growth-reading-list.md --expected-n 10 --expected-language en"
        ),
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        required=True,
        help="Path to the Markdown reading list to validate.",
    )
    parser.add_argument(
        "--expected-n",
        type=int,
        default=None,
        help="Expected number of papers in the reading list.",
    )
    parser.add_argument(
        "--expected-language",
        choices=("en", "zh"),
        default=None,
        help="Expected language of summaries and 'Why Irreplaceable' sections.",
    )
    args = parser.parse_args(argv)

    md_text = args.input.read_text(encoding="utf-8")
    report = validate(
        md_text,
        md_path=args.input,
        expected_n=args.expected_n,
        expected_language=args.expected_language,
    )

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
