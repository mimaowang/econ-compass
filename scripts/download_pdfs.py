#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
download_pdfs.py

Download open-access PDFs for papers in an econ-compass Markdown reading list.

The script uses a multi-source fallback chain inspired by several open-source
academic-paper downloaders (see ``REFERENCES`` below). For each paper it tries,
in order:

    1. Unpaywall (best_oa_location.url_for_pdf)
    2. Semantic Scholar (openAccessPdf.url)
    3. OpenAlex (best_oa_location.pdf_url)
    4. arXiv (title + first-author search)

Only *published-version* open-access PDFs are accepted automatically. Preprints,
accepted manuscripts, and working-paper versions are deliberately skipped so the
downloaded file matches the cited journal article. Papers that cannot be
auto-downloaded are still given a direct access link (DOI resolver or publisher
landing page) in ``unavailable-papers.md`` so users can retrieve them through
their institutional subscriptions.

Only legal open-access routes are used; no paywalls are bypassed.

REFERENCES
----------
- paper-fetch (https://github.com/Agents365-ai/paper-fetch): 7-source DOI → PDF
  resolver with Unpaywall, Semantic Scholar, arXiv, PMC, bioRxiv, publisher OA
  and Sci-Hub fallback chain.
- scholar-megasearch (https://github.com/TaewoooPark/scholar-megasearch):
  multi-source academic search that acquires PDFs via open-access routes across
  20+ databases.
- scholar-mcp (https://github.com/ms7679-1/scholar-mcp): local MCP server with
  Unpaywall → Publisher OA → arXiv fallback for paper downloads.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen


UNPAYWALL_API = "https://api.unpaywall.org/v2/{doi}"
SEMANTIC_SCHOLAR_API = (
    "https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}"
    "?fields=openAccessPdf,url"
)
OPENALEX_API = "https://api.openalex.org/works/doi:{doi}"
ARXIV_API = "https://export.arxiv.org/api/query"

USER_AGENT = (
    "econ-compass-pdf-downloader/2.0 "
    "(https://github.com/mimaowang/econ-compass; mailto:{email})"
)

# Characters that are illegal in Windows or problematic in cross-platform filenames.
INVALID_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|]')

# Minimum delay between requests to the same upstream API (seconds).
_MIN_API_INTERVAL = 0.5

# Last-call timestamps per host for polite rate limiting.
_last_api_call: Dict[str, float] = {}
_last_api_lock = Lock()

_PREPRINT_HOST_FRAGMENTS = (
    "arxiv.org",
    "biorxiv.org",
    "medrxiv.org",
    "ssrn.com",
    "nber.org",
    "repec.org",
    "ideas.repec.org",
    "econpapers.repec.org",
)


def _url_host(url: Optional[str]) -> str:
    """Return a normalized URL host, or an empty string for malformed URLs."""
    if not url:
        return ""
    return urlparse(url).netloc.lower()


def _is_preprint_or_working_paper_url(url: Optional[str]) -> bool:
    """Return True for known preprint or working-paper repositories."""
    if not url:
        return False
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    if any(fragment in host for fragment in _PREPRINT_HOST_FRAGMENTS):
        return True
    return "nber.org" in host and "/papers" in path


def _clean_filename_part(text: Optional[str], max_len: int = 80) -> str:
    """Sanitize a string so it can be used as part of a filename."""
    if not text:
        return ""
    cleaned = INVALID_FILENAME_CHARS.sub(" ", text)
    cleaned = cleaned.replace("\n", " ").replace("\r", " ")
    cleaned = " ".join(cleaned.split())
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len].rsplit(" ", 1)[0] + "..."
    return cleaned.strip(" ._")


def _extract_papers(md_text: str) -> List[Dict[str, Optional[str]]]:
    """Extract title, authors, and DOI for each paper block."""
    zh_paper = "\u8bba\u6587"
    zh_authors = "\u4f5c\u8005"
    colon_class = ":\\uff1a.\\s\\-\\u2013\\u2014"
    header_re = re.compile(
        rf"^##\s+(?:Paper|{zh_paper})\s*#?\s*\d+[{colon_class}]+\s*(.+)$",
        re.MULTILINE | re.IGNORECASE,
    )
    split_re = re.compile(
        rf"(?=^##\s+(?:Paper|{zh_paper})\s*#?\s*\d+[{colon_class}]+)",
        re.MULTILINE | re.IGNORECASE,
    )
    field_prefix = r"^\s*(?:[-*+]\s*)?\*?\*?\s*"
    field_colon = r"\s*\*?\*?\s*[:\uff1a]\s*(.+)$"

    papers: List[Dict[str, Optional[str]]] = []
    for block in split_re.split(md_text):
        title_match = header_re.search(block)
        if not title_match:
            continue

        def get_field(labels: str) -> Optional[str]:
            pattern = field_prefix + rf"(?:{labels})" + field_colon
            m = re.search(pattern, block, re.IGNORECASE | re.MULTILINE)
            return m.group(1).strip() if m else None

        doi = get_field("DOI")
        if doi:
            doi = doi.strip().rstrip(".,;})]")
            doi = re.sub(r"^(?:https?://doi\.org/|doi:)", "", doi, flags=re.IGNORECASE)

        papers.append(
            {
                "number": len(papers) + 1,
                "title": title_match.group(1).strip(),
                "authors": get_field("|".join(["Authors", zh_authors])),
                "doi": doi,
            }
        )
    return papers


def _filename_author_part(authors_text: Optional[str]) -> str:
    """Return compact author last names for PDF filenames."""
    if not authors_text:
        return ""
    raw_authors = [a.strip() for a in re.split(r"\s*;\s*|\s+and\s+", authors_text) if a.strip()]
    last_names: List[str] = []
    for author in raw_authors:
        if "," in author:
            last = author.split(",", 1)[0].strip()
        else:
            parts = author.split()
            last = parts[-1].strip() if parts else ""
        if last:
            last_names.append(last)
    if len(last_names) > 3:
        return f"{last_names[0]} et al."
    return ", ".join(last_names)


def _pdf_filename(paper: Dict[str, Optional[str]]) -> str:
    """Build a filename like '[01] Full Title - Authors.pdf'."""
    number = paper.get("number") or 0
    title = _clean_filename_part(paper.get("title"), max_len=120)
    authors = _clean_filename_part(_filename_author_part(paper.get("authors")), max_len=60)
    parts = [f"[{number:02d}] {title}"]
    if authors:
        parts.append(f"- {authors}")
    base = " ".join(parts)
    return f"{base}.pdf"


def _polite_delay(host: str, delay: float = _MIN_API_INTERVAL) -> None:
    """Sleep if necessary to avoid hammering a single API host."""
    if not host:
        return
    with _last_api_lock:
        now = time.monotonic()
        last = _last_api_call.get(host, 0.0)
        elapsed = now - last
        if elapsed < delay:
            time.sleep(delay - elapsed)
        _last_api_call[host] = time.monotonic()


def _http_get_json(url: str, email: str, timeout: float = 30.0) -> Optional[Dict]:
    """Fetch JSON from ``url`` with polite rate limiting and standard headers."""
    host = _url_host(url)
    if not host:
        return None
    _polite_delay(host)
    req = Request(url)
    req.add_header("User-Agent", USER_AGENT.format(email=email))
    req.add_header("Accept", "application/json")
    try:
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return None


def _http_get_text(url: str, email: str, timeout: float = 30.0) -> Optional[str]:
    """Fetch text from ``url`` with polite rate limiting."""
    host = _url_host(url)
    if not host:
        return None
    _polite_delay(host)
    req = Request(url)
    req.add_header("User-Agent", USER_AGENT.format(email=email))
    req.add_header("Accept", "application/atom+xml, application/xml, text/xml, */*")
    try:
        with urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except (HTTPError, URLError, TimeoutError):
        return None


def _unpaywall_result(doi: str, email: str) -> Dict[str, Optional[str]]:
    """Return Unpaywall OA result (PDF URL, version, landing page) for ``doi``."""
    url = UNPAYWALL_API.format(doi=quote(doi, safe=""))
    data = _http_get_json(f"{url}?email={quote(email)}", email)
    if not data:
        return {}
    loc = data.get("best_oa_location") or {}
    return {
        "url": loc.get("url_for_pdf"),
        "version": loc.get("version"),
        "landing_page": loc.get("url_for_landing_page") or loc.get("url"),
    }


def _semantic_scholar_result(doi: str, email: str) -> Dict[str, Optional[str]]:
    """Return Semantic Scholar OA result for ``doi``."""
    url = SEMANTIC_SCHOLAR_API.format(doi=quote(doi, safe=""))
    data = _http_get_json(url, email)
    if not data:
        return {}
    oa = data.get("openAccessPdf") or {}
    pdf_url = oa.get("url")
    version: Optional[str] = None
    if pdf_url and _is_preprint_or_working_paper_url(pdf_url):
        version = "submittedVersion"
    return {
        "url": pdf_url,
        "version": version,
        "landing_page": data.get("url"),
    }


def _openalex_result(doi: str, email: str) -> Dict[str, Optional[str]]:
    """Return OpenAlex OA result for ``doi``."""
    url = OPENALEX_API.format(doi=quote(doi, safe=""))
    data = _http_get_json(url, email)
    if not data:
        return {}
    best = data.get("best_oa_location") or {}
    pdf_url = best.get("pdf_url")
    version = best.get("version")
    if not pdf_url:
        for loc in data.get("locations", []):
            if loc.get("pdf_url"):
                pdf_url = loc["pdf_url"]
                version = loc.get("version") or version
                break
    landing_page = (
        best.get("landing_page_url")
        or (data.get("primary_location") or {}).get("landing_page_url")
    )
    return {
        "url": pdf_url,
        "version": version,
        "landing_page": landing_page,
    }


def _arxiv_pdf_url(title: str, first_author: str, email: str) -> Optional[str]:
    """Search arXiv by title + first author and return a PDF URL if matched."""
    if not title:
        return None
    # Build a conservative query and let urlencode perform exactly one encoding pass.
    query_parts = [f'ti:"{title}"']
    if first_author:
        query_parts.append(f'au:"{first_author}"')
    query = "+AND+".join(query_parts)
    params = {"search_query": query, "start": 0, "max_results": 5}
    url = f"{ARXIV_API}?{urlencode(params)}"
    text = _http_get_text(url, email)
    if not text:
        return None

    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return None

    # Atom namespace.
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.findall("atom:entry", ns):
        # Skip the generic "opensearch:totalResults" pseudo-entry.
        if entry.find("atom:title", ns) is None:
            continue
        pdf_link = entry.find("atom:link[@title='pdf']", ns)
        if pdf_link is not None:
            href = pdf_link.get("href")
            if href:
                return href
        # Some feeds use rel="related" with title/type instead.
        for link in entry.findall("atom:link", ns):
            if link.get("type") == "application/pdf":
                href = link.get("href")
                if href:
                    return href
    return None


def _arxiv_result(title: str, first_author: str, email: str) -> Dict[str, Optional[str]]:
    """Return arXiv result; arXiv is always a preprint/working-paper version."""
    pdf_url = _arxiv_pdf_url(title, first_author, email)
    if not pdf_url:
        return {}
    # Convert https://arxiv.org/pdf/2101.00001.pdf -> https://arxiv.org/abs/2101.00001
    landing_page = pdf_url.replace("/pdf/", "/abs/").removesuffix(".pdf")
    return {
        "url": pdf_url,
        "version": "submittedVersion",
        "landing_page": landing_page,
    }


def _first_author_last_name(authors_text: Optional[str]) -> str:
    """Extract the probable last name of the first author."""
    if not authors_text:
        return ""
    first = authors_text.split(";")[0].strip()
    if "," in first:
        return first.split(",")[0].strip()
    parts = first.split()
    return parts[-1].strip() if parts else ""


def _is_published_version(version: Optional[str], url: Optional[str] = None) -> bool:
    """Return True if ``version`` and ``url`` indicate the published version."""
    if _is_preprint_or_working_paper_url(url):
        return False
    if not version:
        return True
    return version == "publishedVersion"


def _resolve_source_results(
    paper: Dict[str, Optional[str]],
    email: str,
    enabled_sources: List[str],
) -> Dict[str, Dict[str, Optional[str]]]:
    """Query every enabled source and return its result dict."""
    doi = paper.get("doi")
    title = paper.get("title") or ""
    first_author = _first_author_last_name(paper.get("authors"))

    results: Dict[str, Dict[str, Optional[str]]] = {}
    if doi and "unpaywall" in enabled_sources:
        results["unpaywall"] = _unpaywall_result(doi, email)
    if doi and "semanticscholar" in enabled_sources:
        results["semanticscholar"] = _semantic_scholar_result(doi, email)
    if doi and "openalex" in enabled_sources:
        results["openalex"] = _openalex_result(doi, email)
    if "arxiv" in enabled_sources:
        results["arxiv"] = _arxiv_result(title, first_author, email)
    return results


def _resolve_manual_link(
    doi: Optional[str],
    results: Dict[str, Dict[str, Optional[str]]],
) -> Tuple[Optional[str], Optional[str]]:
    """Return a direct access link for papers that cannot be auto-downloaded.

    Priority:
        1. DOI resolver (most reliable; jumps to publisher page)
        2. Any source's landing page
        3. Any source's OA PDF URL (last resort; may be a direct PDF)
    """
    if doi:
        return f"https://doi.org/{doi}", "doi_resolver"
    for result in results.values():
        landing = result.get("landing_page")
        if landing:
            return landing, "landing_page"
    for source, result in results.items():
        url = result.get("url")
        if url:
            return url, f"{source}_oa_pdf"
    return None, None


def _download_pdf(url: str, dest: Path, email: str) -> bool:
    """Download a PDF from an open-access URL to ``dest``.

    Validates that the response is actually a PDF by checking the Content-Type
    header or the file magic bytes.
    """
    host = _url_host(url)
    if not host:
        return False
    _polite_delay(host, delay=0.2)
    req = Request(url)
    req.add_header("User-Agent", USER_AGENT.format(email=email))
    req.add_header("Accept", "application/pdf, application/octet-stream, */*")
    try:
        with urlopen(req, timeout=60.0) as resp:
            data = resp.read()
            if not data.startswith(b"%PDF"):
                return False
            # The PDF magic bytes are the authoritative check; repositories
            # sometimes serve valid PDFs with generic Content-Type values.
            dest.write_bytes(data)
        return True
    except (HTTPError, URLError, TimeoutError, OSError):
        return False


def _process_paper(
    paper: Dict[str, Optional[str]],
    output_dir: Path,
    email: str,
    enabled_sources: List[str],
) -> Dict:
    """Resolve and download a single paper's PDF."""
    record: Dict = {
        "number": paper.get("number"),
        "title": paper.get("title"),
        "authors": paper.get("authors"),
        "doi": paper.get("doi"),
        "filename": None,
        "source": None,
        "version": None,
        "status": "pending",
        "manual_link": None,
        "link_type": None,
        "reason": None,
    }

    results = _resolve_source_results(paper, email, enabled_sources)
    manual_link, link_type = _resolve_manual_link(paper.get("doi"), results)
    record["manual_link"] = manual_link
    record["link_type"] = link_type

    downloaded = False
    tried_sources: List[str] = []
    skipped_version_reasons: List[str] = []

    for source in enabled_sources:
        result = results.get(source)
        if not result:
            continue
        url = result.get("url")
        version = result.get("version")
        if not url:
            continue
        tried_sources.append(source)

        if _is_published_version(version, url):
            filename = _pdf_filename(paper)
            dest = output_dir / filename
            if _download_pdf(url, dest, email):
                record["status"] = "downloaded"
                record["filename"] = filename
                record["source"] = source
                record["version"] = version or "unknown"
                downloaded = True
                break
            record["reason"] = f"Found published-version URL via {source}, but PDF download failed."
        else:
            skipped_version_reasons.append(
                f"{source} returned {version}; skipped to avoid non-published version"
            )

    if not downloaded:
        base_reason = record.get("reason") or "No open-access published-version PDF found."
        if skipped_version_reasons:
            joined = "; ".join(skipped_version_reasons)
            record["reason"] = f"Skipped non-published versions ({joined}); {base_reason}"
        else:
            record["reason"] = base_reason

        if manual_link:
            record["status"] = "manual_link"
        else:
            record["status"] = "unavailable"
            record["reason"] = record.get("reason") or "No DOI or access link found."

    return record


def download_pdfs(
    md_text: str,
    output_dir: Path,
    email: str,
    json_report: bool = False,
    sources: Optional[List[str]] = None,
    max_workers: int = 3,
) -> Dict:
    """Download OA PDFs using a multi-source fallback chain.

    Args:
        md_text: Markdown reading-list text.
        output_dir: Directory where PDFs will be saved.
        email: Contact email used in User-Agent and for Unpaywall.
        json_report: If True, include per-paper records in the returned dict.
        sources: Ordered list of source names to query. Defaults to all.
        max_workers: Maximum concurrent paper downloads.

    Returns:
        A dictionary summarizing successes, manual links, failures, and
        unavailable papers.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    papers = _extract_papers(md_text)
    enabled_sources = sources or ["unpaywall", "semanticscholar", "openalex", "arxiv"]

    report: Dict = {
        "total": len(papers),
        "downloaded": 0,
        "manual_link": 0,
        "unavailable": 0,
        "output_dir": output_dir.as_posix(),
        "sources_used": enabled_sources,
        "papers": [],
    }

    records: List[Dict] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_paper = {
            executor.submit(_process_paper, paper, output_dir, email, enabled_sources): paper
            for paper in papers
        }
        for future in as_completed(future_to_paper):
            records.append(future.result())

    records.sort(key=lambda r: (r["number"] or 0))
    not_downloaded = [r for r in records if r["status"] != "downloaded"]

    report["papers"] = records
    report["downloaded"] = sum(1 for r in records if r["status"] == "downloaded")
    report["manual_link"] = sum(1 for r in records if r["status"] == "manual_link")
    report["unavailable"] = sum(1 for r in records if r["status"] == "unavailable")
    report["not_downloaded"] = not_downloaded

    if not_downloaded:
        attention_path = output_dir / "unavailable-papers.md"
        _write_attention_md(attention_path, not_downloaded)
        report["attention_path"] = attention_path.as_posix()

    if not json_report:
        report.pop("papers", None)

    return report


def _md_cell(value: object) -> str:
    """Escape a value for use inside a Markdown table cell."""
    text = str(value or "")
    text = text.replace("\r", " ").replace("\n", " ")
    return text.replace("|", "\\|").strip()


def _write_attention_md(path: Path, records: List[Dict]) -> None:
    """Write the unavailable-papers Markdown report.

    Includes papers that could not be auto-downloaded as published versions,
    with a direct access link (DOI resolver or publisher landing page) so the
    user can retrieve them through their institutional subscription.
    """
    lines: List[str] = [
        "# Papers That Could Not Be Auto-Downloaded",
        "",
        "> Generated by econ-compass download_pdfs.py. The following papers could not be "
        "automatically downloaded as the published-journal PDF. For each paper a direct "
        "access link is provided so you can view or download it through your institution "
        "or publisher subscription.",
        "",
        "| # | Title | Authors | DOI | Status | Manual Link | Source Tried | Reason |",
        "|---|-------|---------|-----|--------|-------------|--------------|--------|",
    ]
    for record in records:
        number = _md_cell(record.get("number") or "")
        title = _md_cell(record.get("title") or "")
        authors = _md_cell(record.get("authors") or "")
        doi = _md_cell(record.get("doi") or "")
        status = _md_cell(record.get("status") or "")
        manual_link = _md_cell(record.get("manual_link") or "")
        source = _md_cell(record.get("source") or "-")
        reason = _md_cell(record.get("reason") or "")
        lines.append(
            f"| {number} | {title} | {authors} | {doi} | {status} | {manual_link} | {source} | {reason} |"
        )

    lines.extend(
        [
            "",
            "## How to use the Manual Link",
            "- **doi_resolver**: The DOI resolver (`https://doi.org/...`) redirects to the "
            "publisher's official article page, where you can usually view the abstract and "
            "download the PDF if your institution has a subscription.",
            "- **landing_page**: A publisher or repository page for the article.",
            "- **{source}_oa_pdf**: A direct open-access PDF URL that the script did not use "
            "because it appeared to be a preprint or non-published version.",
            "",
            "## Suggestions",
            "- Open the DOI resolver link while connected to your university/library network or VPN.",
            "- If the link redirects to a paywall, request the paper through your library's interlibrary loan.",
            "- Check ResearchGate or the author's personal website only if you cannot access the publisher version.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Download open-access PDFs for papers in an econ-compass Markdown reading list. "
            "Uses a multi-source fallback chain (Unpaywall → Semantic Scholar → OpenAlex → arXiv) "
            "and only keeps published-journal versions."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/download_pdfs.py -i growth-reading-list.md\n"
            "  python scripts/download_pdfs.py -i growth-reading-list.md -o ./my-pdfs --email user@example.edu\n"
            "  python scripts/download_pdfs.py -i growth.md --sources semanticscholar,openalex\n"
            "  set UNPAYWALL_EMAIL=user@example.edu && python scripts/download_pdfs.py -i growth.md"
        ),
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        required=True,
        help="Path to the Markdown reading list.",
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=Path("./pdfs"),
        help="Directory where PDFs will be saved (default: ./pdfs/).",
    )
    parser.add_argument(
        "--email",
        type=str,
        default=None,
        help="Contact email for Unpaywall and User-Agent (default: UNPAYWALL_EMAIL env var).",
    )
    parser.add_argument(
        "--sources",
        type=str,
        default=None,
        help="Comma-ordered source list, e.g. unpaywall,semanticscholar,openalex,arxiv (default: all).",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=3,
        help="Maximum concurrent downloads (default: 3).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output a JSON report instead of a short summary.",
    )
    args = parser.parse_args(argv)

    email = args.email or os.environ.get("UNPAYWALL_EMAIL")
    if not email:
        print(
            "Error: A contact email is required. Provide --email or set the "
            "UNPAYWALL_EMAIL environment variable.",
            file=sys.stderr,
        )
        return 1

    if not args.input.exists():
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        return 1

    sources: Optional[List[str]] = None
    if args.sources:
        sources = [s.strip().lower() for s in args.sources.split(",") if s.strip()]
        valid = {"unpaywall", "semanticscholar", "openalex", "arxiv"}
        invalid = [s for s in sources if s not in valid]
        if invalid:
            print(f"Error: invalid source(s): {', '.join(invalid)}", file=sys.stderr)
            return 1

    md_text = args.input.read_text(encoding="utf-8")
    report = download_pdfs(
        md_text,
        output_dir=args.output_dir,
        email=email,
        json_report=args.json,
        sources=sources,
        max_workers=args.max_workers,
    )

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(
            f"Downloaded {report['downloaded']}/{report['total']} PDFs to "
            f"{report['output_dir']}"
        )
        if report["manual_link"]:
            print(
                f"{report['manual_link']} paper(s) need manual download; direct links saved in "
                f"{report.get('attention_path', 'unavailable-papers.md')}"
            )
        if report["unavailable"]:
            print(
                f"{report['unavailable']} paper(s) unavailable. See "
                f"{report.get('attention_path', 'unavailable-papers.md')}"
            )

    return 0 if report["unavailable"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
