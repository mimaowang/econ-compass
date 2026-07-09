#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_pdf_download.py

Benchmark the PDF download capability of econ-compass.

Usage
-----
    # Live mode: requires a valid contact email
    python benchmark/scripts/test_pdf_download.py --mode live --email your@email.edu

    # Mock mode: deterministic pipeline test without network calls
    python benchmark/scripts/test_pdf_download.py --mode mock

The fixture ``benchmark/public/fixtures/pdf-download-fixture.md`` contains 10
canonical economics papers. The multi-source downloader tries, in order:
Unpaywall → Semantic Scholar → OpenAlex → arXiv. Only *published* versions are
kept; preprints/working papers are skipped and reported as manual links. The
test reports how many OA PDFs can be auto-downloaded and provides direct access
links for the rest.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import download_pdfs from the project scripts directory.
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from download_pdfs import download_pdfs  # noqa: E402


FIXTURE_PATH = ROOT / "benchmark" / "public" / "fixtures" / "pdf-download-fixture.md"
DEFAULT_OUTPUT_DIR = Path("benchmark/workspace/pdf-download-test")

# Minimum auto-download success rate considered acceptable for the benchmark.
TARGET_SUCCESS_RATE = 0.50


# Realistic mock responses for the 10 fixture papers.
# In mock mode we do not hit the network; these responses exercise every source
# and version path in the download pipeline. The target is ~60% auto-download
# success (6/10), with the remaining papers receiving a direct manual link.
#
# Source legend:
#   U = Unpaywall, S = Semantic Scholar, O = OpenAlex, A = arXiv
#   publishedVersion = kept, submittedVersion/acceptedVersion = skipped
_MOCK_SOURCES: Dict[str, Optional[Dict[str, str]]] = {
    # Acemoglu, Johnson, Robinson (2001) AER — publisher OA via Unpaywall
    "10.1257/aer.91.5.1369": {"source": "unpaywall", "version": "publishedVersion"},
    # Card & Krueger (1994) AER — publisher OA via Semantic Scholar
    "10.1257/aer.84.4.772": {"source": "semanticscholar", "version": "publishedVersion"},
    # Duflo et al. (2011) AER — gold OA in Unpaywall
    "10.1257/aer.101.6.2350": {"source": "unpaywall", "version": "publishedVersion"},
    # Laibson (1997) QJE — only an arXiv preprint exists; must be skipped
    "10.1162/003355397555253": {"source": "arxiv", "version": "submittedVersion"},
    # Kahneman & Tversky (1979) Econometrica — no OA anywhere
    "10.2307/1914185": None,
    # Rosenbaum & Rubin (1983) Biometrika — hybrid OA in OpenAlex
    "10.1093/biomet/70.1.41": {"source": "openalex", "version": "publishedVersion"},
    # Abadie et al. (2010) JASA — gold OA in Unpaywall
    "10.1198/jasa.2009.ap08746": {"source": "unpaywall", "version": "publishedVersion"},
    # Angrist & Krueger (1991) QJE — no OA
    "10.2307/2937954": None,
    # Bertrand, Duflo, Mullainathan (2004) QJE — no OA
    "10.1162/003355304772839588": None,
    # Chetty et al. (2014) AER — gold OA in Unpaywall
    "10.1257/aer.104.9.2593": {"source": "unpaywall", "version": "publishedVersion"},
}


def _mock_url(doi: str) -> str:
    """Build a deterministic fake PDF URL for a DOI."""
    return f"https://mock-oa.example.com/{doi.replace('/', '_')}.pdf"


def _install_mock() -> None:
    """Monkey-patch source lookups so the test does not use the network."""
    import download_pdfs as dp

    def _mock_unpaywall_result(doi: str, email: str) -> Dict[str, Optional[str]]:
        cfg = _MOCK_SOURCES.get(doi)
        if cfg and cfg["source"] == "unpaywall":
            return {
                "url": _mock_url(doi),
                "version": cfg["version"],
                "landing_page": f"https://mock-landing.example.com/{doi}",
            }
        return {}

    def _mock_semantic_scholar_result(doi: str, email: str) -> Dict[str, Optional[str]]:
        cfg = _MOCK_SOURCES.get(doi)
        if cfg and cfg["source"] == "semanticscholar":
            return {
                "url": _mock_url(doi),
                "version": cfg["version"],
                "landing_page": f"https://mock-landing.example.com/{doi}",
            }
        return {}

    def _mock_openalex_result(doi: str, email: str) -> Dict[str, Optional[str]]:
        cfg = _MOCK_SOURCES.get(doi)
        if cfg and cfg["source"] == "openalex":
            return {
                "url": _mock_url(doi),
                "version": cfg["version"],
                "landing_page": f"https://mock-landing.example.com/{doi}",
            }
        return {}

    def _mock_arxiv_result(title: str, first_author: str, email: str) -> Dict[str, Optional[str]]:
        # Match mock arXiv preprint by title substring.
        if title and "hyperbolic discounting" in title.lower():
            doi = "10.1162/003355397555253"
            cfg = _MOCK_SOURCES[doi]
            return {
                "url": _mock_url(doi),
                "version": cfg["version"],
                "landing_page": f"https://mock-landing.example.com/{doi}",
            }
        return {}

    dp._unpaywall_result = _mock_unpaywall_result
    dp._semantic_scholar_result = _mock_semantic_scholar_result
    dp._openalex_result = _mock_openalex_result
    dp._arxiv_result = _mock_arxiv_result


def _install_mock_downloader() -> None:
    """
    Monkey-patch PDF download to simulate success for mock OA URLs.
    We create a tiny valid-ish PDF byte header so content-type checks pass.
    """
    import download_pdfs as dp

    _real_download_pdf = dp._download_pdf

    def _mock_download_pdf(url: str, dest: Path, email: str) -> bool:
        if url.startswith("https://mock-oa.example.com/"):
            # Minimal PDF header so the script believes it is a PDF.
            dest.write_bytes(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n")
            return True
        return _real_download_pdf(url, dest, email)

    dp._download_pdf = _mock_download_pdf


def _build_markdown_report(report: Dict[str, Any], mode: str, email: Optional[str]) -> str:
    """Render the JSON report as Markdown."""
    total = report["total"]
    downloaded = report["downloaded"]
    manual_link = report.get("manual_link", 0)
    unavailable = report.get("unavailable", 0)
    auto_rate = downloaded / total * 100 if total else 0.0
    any_access_rate = (downloaded + manual_link) / total * 100 if total else 0.0

    lines: List[str] = [
        "# PDF Download Benchmark Report",
        "",
        f"- **Mode:** {mode}",
        f"- **Fixture:** {FIXTURE_PATH.name} (10 canonical papers)",
        f"- **Email used:** {email or '(not set)'}",
        f"- **Sources tried:** {', '.join(report.get('sources_used', []))}",
        f"- **Timestamp:** {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total papers | {total} |",
        f"| Downloaded (published version) | {downloaded} |",
        f"| Manual link provided | {manual_link} |",
        f"| Unavailable | {unavailable} |",
        f"| Auto-download success rate | {auto_rate:.1f}% |",
        f"| Access rate (auto + manual link) | {any_access_rate:.1f}% |",
        f"| Target auto-download rate | {TARGET_SUCCESS_RATE * 100:.0f}% |",
        "",
        "## Per-Paper Results",
        "",
        "| # | Title | DOI | Status | Source | Version | Manual Link | Reason |",
        "|---|-------|-----|--------|--------|---------|-------------|--------|",
    ]

    for paper in report["papers"]:
        reason = paper.get("reason") or "-"
        source = paper.get("source") or "-"
        version = paper.get("version") or "-"
        link = paper.get("manual_link") or "-"
        lines.append(
            f"| {paper['number']} | {paper['title'][:55]} | {paper['doi'] or '-'} | "
            f"{paper['status']} | {source} | {version} | {link} | {reason} |"
        )

    lines.extend([
        "",
        "## Why Papers Could Not Be Auto-Downloaded",
        "",
    ])

    reasons: Dict[str, int] = {}
    for paper in report["papers"]:
        if paper["status"] != "downloaded":
            reason = paper.get("reason") or "Unknown"
            reasons[reason] = reasons.get(reason, 0) + 1

    if reasons:
        for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):
            lines.append(f"- **{reason}**: {count} paper(s)")
    else:
        lines.append("- All papers downloaded successfully.")

    lines.extend([
        "",
        "## Interpretation",
        "",
        "- **downloaded**: A published-version open-access PDF was found and saved.",
        "- **manual_link**: No published-version OA PDF was found automatically, but a direct "
        "link (usually the DOI resolver) is provided so the user can retrieve the paper through "
        "their institutional subscription.",
        "- **unavailable**: No DOI or access link could be determined.",
        "- **Preprint skipped**: A source returned a non-published version (e.g., arXiv preprint or "
        "accepted manuscript). It is intentionally excluded from auto-download to avoid mismatched "
        "versions, but a manual link is still provided.",
        "",
        "## Re-run against Real APIs",
        "",
        "To run this benchmark with live network calls, provide a valid email:",
        "",
        "```bash",
        f"python {Path(__file__).relative_to(ROOT).as_posix()} --mode live --email your@email.edu",
        "```",
        "",
    ])

    return "\n".join(lines) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Benchmark PDF download success rate for econ-compass.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python benchmark/scripts/test_pdf_download.py --mode mock\n"
            "  python benchmark/scripts/test_pdf_download.py --mode live --email your@email.edu\n"
            "  set UNPAYWALL_EMAIL=your@email.edu && python benchmark/scripts/test_pdf_download.py --mode live"
        ),
    )
    parser.add_argument(
        "--mode",
        choices=["live", "mock"],
        default="mock",
        help="Run against real APIs or use deterministic mocks (default: mock).",
    )
    parser.add_argument(
        "--email",
        type=str,
        default=None,
        help="Contact email for APIs. Required for live mode; can also use UNPAYWALL_EMAIL env var.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for downloaded PDFs and reports.",
    )
    args = parser.parse_args(argv)

    if not FIXTURE_PATH.exists():
        print(f"Error: fixture not found: {FIXTURE_PATH}", file=sys.stderr)
        return 1

    email = args.email or os.environ.get("UNPAYWALL_EMAIL")

    if args.mode == "live" and not email:
        print(
            "Error: live mode requires a valid email. "
            "Provide --email or set the UNPAYWALL_EMAIL environment variable.",
            file=sys.stderr,
        )
        return 1

    if args.mode == "mock":
        _install_mock()
        _install_mock_downloader()
        email = email or "mock@example.com"

    md_text = FIXTURE_PATH.read_text(encoding="utf-8")
    report = download_pdfs(
        md_text,
        output_dir=args.output_dir,
        email=email,
        json_report=True,
    )

    # Add benchmark metadata.
    report["mode"] = args.mode
    report["email_used"] = email if args.mode == "live" else "(mock)"
    report["fixture"] = "benchmark/public/fixtures/pdf-download-fixture.md"
    report["timestamp"] = datetime.now(timezone.utc).isoformat()
    report["target_success_rate"] = TARGET_SUCCESS_RATE

    args.output_dir.mkdir(parents=True, exist_ok=True)
    report_path = args.output_dir / "pdf-download-report.json"
    report_md_path = args.output_dir / "pdf-download-report.md"

    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    md_report = _build_markdown_report(report, args.mode, report["email_used"])
    report_md_path.write_text(md_report, encoding="utf-8")

    print(md_report)
    print(f"JSON report: {report_path}")
    print(f"Markdown report: {report_md_path}")

    # Pass if the auto-download rate meets the target.
    auto_rate = report["downloaded"] / report["total"] if report["total"] else 0.0
    return 0 if auto_rate >= TARGET_SUCCESS_RATE else 1


if __name__ == "__main__":
    sys.exit(main())
