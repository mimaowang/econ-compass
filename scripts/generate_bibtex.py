#!/usr/bin/env python3
"""
generate_bibtex.py

Read an econ-compass Markdown reading list and emit a standard BibTeX file.

This is a real executable tool, not a prompt instruction. It can be imported
as a module (``generate_bibtex(md_text)``) or invoked from the command line.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable, List, Optional


STOP_WORDS = {"the", "a", "an"}

ZH_PAPER = "\u8bba\u6587"
ZH_AUTHORS = "\u4f5c\u8005"
ZH_YEAR = "\u5e74\u4efd"
ZH_JOURNAL = "\u671f\u520a"
ZH_VOLUME = "\u5377"
ZH_NUMBER = "\u671f"
ZH_PAGES = "\u9875\u7801"
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


def _extract_papers(md_text: str) -> List[dict]:
    """Parse the Markdown text and return a list of paper dictionaries."""
    papers: List[dict] = []
    # Split on paper headings while keeping the heading in each block. This is
    # more reliable than requiring horizontal-rule separators between papers.
    blocks = _PAPER_SPLIT_RE.split(md_text)
    for block in blocks:
        paper = _parse_paper_block(block)
        if paper:
            papers.append(paper)
    return papers


def _parse_paper_block(block: str) -> Optional[dict]:
    """Parse a single paper block into a dictionary of metadata."""
    title_match = _PAPER_HEADER_RE.search(block)
    if not title_match:
        return None

    title = title_match.group(1).strip()

    def get_field(labels: str) -> Optional[str]:
        pattern = _BULLET_PREFIX + rf"(?:{labels})" + _BOLD_COLON + r"(.+)$"
        m = re.search(pattern, block, re.IGNORECASE | re.MULTILINE)
        return m.group(1).strip() if m else None

    authors_raw = get_field("|".join(["Authors", ZH_AUTHORS]))
    year = get_field("|".join(["Year", ZH_YEAR]))
    journal = get_field("|".join(["Journal", ZH_JOURNAL]))
    volume = get_field("|".join(["Volume", ZH_VOLUME]))
    number = get_field("|".join(["Number", ZH_NUMBER]))
    pages = get_field("|".join(["Pages", ZH_PAGES]))
    doi = get_field(r"DOI")

    if doi:
        doi = doi.strip().rstrip(".,;})]")
        doi = re.sub(r"^(?:https?://doi\.org/|doi:)", "", doi, flags=re.IGNORECASE)

    return {
        "title": title,
        "authors": authors_raw,
        "year": year,
        "journal": journal,
        "volume": volume,
        "number": number,
        "pages": pages,
        "doi": doi,
    }


def _convert_authors(authors_raw: Optional[str]) -> str:
    """Convert 'Last, First; Last, First' to BibTeX 'Last, First and Last, First'."""
    if not authors_raw:
        return ""
    parts = re.split(r"\s*;\s*|\s+and\s+", authors_raw, flags=re.IGNORECASE)
    authors = [p.strip() for p in parts if p.strip()]
    return " and ".join(authors)


def _first_author_last(authors_raw: Optional[str]) -> str:
    """Return the last name of the first author, lowercased and key-safe."""
    if not authors_raw:
        return "unknown"
    first = re.split(r"\s*;\s*|\s+and\s+", authors_raw, flags=re.IGNORECASE)[0].strip()
    if "," in first:
        last = first.split(",", 1)[0].strip()
    else:
        parts = first.split()
        last = parts[-1].strip() if parts else "unknown"
    cleaned = re.sub(r"[^a-z0-9]", "", last.lower())
    return cleaned or "unknown"


def _first_title_word(title: str) -> str:
    """Return the first non-stop-word of the title, lowercased and cleaned."""
    words = re.findall(r"[A-Za-z0-9]+", title)
    for word in words:
        w = word.lower()
        if w not in STOP_WORDS:
            return re.sub(r"[^a-z0-9]", "", w)
    if words:
        return re.sub(r"[^a-z0-9]", "", words[0].lower())
    return "paper"


def _make_bibtex_key(paper: dict) -> str:
    """Build a BibTeX key in the form LastNameYearFirstWord."""
    last = _first_author_last(paper.get("authors"))
    year = paper.get("year") or "0000"
    word = _first_title_word(paper.get("title", ""))
    return f"{last}{year}{word}"


def _unique_keys(papers: List[dict]) -> List[str]:
    """Assign unique BibTeX keys, appending a/b/c/... on collisions."""
    keys: List[str] = []
    counts: dict = {}
    for paper in papers:
        base = _make_bibtex_key(paper)
        if base in counts:
            counts[base] += 1
            key = f"{base}{chr(ord('a') + counts[base] - 1)}"
        else:
            counts[base] = 1
            key = base
        keys.append(key)
    return keys


def _bibtex_escape(value: Optional[str]) -> str:
    """Minimal BibTeX escaping for braces and common LaTeX special chars."""
    if not value:
        return ""
    escaped = value.replace("\\", "\\\\")
    for char in ("{", "}", "&", "%", "$", "#", "_"):
        escaped = escaped.replace(char, f"\\{char}")
    return escaped


def generate_bibtex(md_text: str) -> str:
    """Convert Markdown reading-list text to a BibTeX string.

    Args:
        md_text: Full Markdown text of a reading list.

    Returns:
        A standard BibTeX string containing ``@article`` entries.
    """
    papers = _extract_papers(md_text)
    if not papers:
        return "% No papers found in the provided Markdown.\n"

    keys = _unique_keys(papers)
    lines: List[str] = []

    for paper, key in zip(papers, keys):
        authors = _convert_authors(paper.get("authors"))
        lines.append(f"@article{{{key},")
        lines.append(f"  title   = {{{_bibtex_escape(paper.get('title'))}}},")
        lines.append(f"  author  = {{{_bibtex_escape(authors)}}},")
        if paper.get("journal"):
            lines.append(f"  journal = {{{_bibtex_escape(paper.get('journal'))}}},")
        if paper.get("year"):
            lines.append(f"  year    = {{{paper.get('year')}}},")
        if paper.get("volume"):
            lines.append(f"  volume  = {{{_bibtex_escape(paper.get('volume'))}}},")
        if paper.get("number"):
            lines.append(f"  number  = {{{_bibtex_escape(paper.get('number'))}}},")
        if paper.get("pages"):
            lines.append(f"  pages   = {{{_bibtex_escape(paper.get('pages'))}}},")
        if paper.get("doi"):
            lines.append(f"  doi     = {{{paper.get('doi')}}}")
        lines.append("}")
        lines.append("")

    return "\n".join(lines)


def _default_output_path(input_path: Optional[Path]) -> Optional[Path]:
    """Return a .bib path next to the input file, or None for stdout."""
    if not input_path:
        return None
    return input_path.with_suffix(".bib")


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a standard BibTeX file from an econ-compass Markdown reading list."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/generate_bibtex.py -i growth-reading-list.md\n"
            "  cat growth-reading-list.md | python scripts/generate_bibtex.py -o growth.bib\n"
            "  python scripts/generate_bibtex.py < growth.md > growth.bib"
        ),
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=None,
        help="Path to the Markdown reading list. If omitted, reads from stdin.",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help=(
            "Path for the generated BibTeX file. If omitted and input is given, "
            "writes to a .bib file next to the input; otherwise writes to stdout."
        ),
    )
    args = parser.parse_args(argv)

    if args.input:
        md_text = args.input.read_text(encoding="utf-8")
    else:
        md_text = sys.stdin.read()

    bibtex = generate_bibtex(md_text)

    output_path = args.output
    if output_path is None and args.input:
        output_path = _default_output_path(args.input)

    if output_path:
        output_path.write_text(bibtex, encoding="utf-8")
        print(f"Wrote BibTeX to {output_path}", file=sys.stderr)
    else:
        sys.stdout.write(bibtex)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
