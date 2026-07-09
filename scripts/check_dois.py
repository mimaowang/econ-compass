#!/usr/bin/env python3
"""
check_dois.py

Batch-verify DOIs extracted from an econ-compass Markdown reading list or a
BibTeX file. Each unique DOI is resolved via https://doi.org/{doi} with a GET
request. Results are cached in-memory, deduplicated, and emitted as JSON.

Exit codes:
  0  All DOIs resolved successfully (HTTP 200).
  1  At least one DOI was invalid, timed out, or returned an unexpected status.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DOI_PATTERN = re.compile(
    r"(?:https?://doi\.org/)?(10\.\d{4,}(?:\.\d+)*/\S+)",
    re.IGNORECASE,
)

# Some publishers reject the default Python UA; use a generic browser UA.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.0 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.0"
)


def _clean_doi(raw: str) -> str:
    """Strip surrounding punctuation and URL prefixes from a DOI."""
    doi = raw.strip().rstrip(".,;})]")
    doi = re.sub(r"^https?://doi\.org/", "", doi, flags=re.IGNORECASE)
    return doi


def _extract_dois_from_markdown(text: str) -> Set[str]:
    """Extract DOIs from a Markdown reading list."""
    dois: Set[str] = set()
    # Common Markdown pattern: **DOI**: https://doi.org/...
    for match in re.finditer(
        r"\*\*DOI\*\*:\s*(.+?)$", text, re.IGNORECASE | re.MULTILINE
    ):
        candidate = _clean_doi(match.group(1))
        if candidate.startswith("10."):
            dois.add(candidate)
    # Fallback: any bare https://doi.org/... or 10.xxxx/...
    for match in DOI_PATTERN.finditer(text):
        candidate = _clean_doi(match.group(1))
        if candidate.startswith("10."):
            dois.add(candidate)
    return dois


def _extract_dois_from_bibtex(text: str) -> Set[str]:
    """Extract DOIs from a BibTeX file using simple regex."""
    dois: Set[str] = set()
    for match in re.finditer(
        r'''doi\s*=\s*["'{]([^"'}]+)["'}]''', text, re.IGNORECASE
    ):
        candidate = _clean_doi(match.group(1))
        if candidate.startswith("10."):
            dois.add(candidate)
    # Also catch any stray https://doi.org/... links.
    for match in DOI_PATTERN.finditer(text):
        candidate = _clean_doi(match.group(1))
        if candidate.startswith("10."):
            dois.add(candidate)
    return dois


def _extract_dois(input_path: Path) -> Set[str]:
    """Dispatch extraction based on file extension."""
    text = input_path.read_text(encoding="utf-8")
    suffix = input_path.suffix.lower()
    if suffix == ".bib":
        return _extract_dois_from_bibtex(text)
    return _extract_dois_from_markdown(text)


def _check_doi(doi: str, timeout: float) -> Dict[str, Optional[str]]:
    """Resolve a single DOI and return a status record."""
    url = f"https://doi.org/{doi}"
    # GET with an Accept header for CSL JSON reduces the chance of publisher
    # blocks and avoids downloading full HTML while still following redirects.
    req = Request(url, method="GET")
    req.add_header("User-Agent", USER_AGENT)
    req.add_header("Accept", "application/vnd.citationstyles.csl+json, application/json, */*")

    try:
        with urlopen(req, timeout=timeout) as resp:
            # Read a small amount to complete the TLS/HTTP handshake.
            _ = resp.read(1)
            status = resp.getcode()
    except HTTPError as exc:
        status = exc.getcode()
    except URLError as exc:
        return {"doi": doi, "status": "error", "code": None, "message": str(exc.reason)}
    except TimeoutError:
        return {"doi": doi, "status": "timeout", "code": None, "message": "Request timed out"}
    except Exception as exc:  # pragma: no cover
        return {"doi": doi, "status": "error", "code": None, "message": str(exc)}

    if status == 200:
        return {"doi": doi, "status": "valid", "code": status, "message": "OK"}
    if status == 404:
        return {"doi": doi, "status": "invalid", "code": status, "message": "DOI not found"}
    return {
        "doi": doi,
        "status": "check",
        "code": status,
        "message": f"Unexpected HTTP status {status}",
    }


def check_dois(dois: Iterable[str], timeout: float = 10.0) -> List[Dict[str, Optional[str]]]:
    """Check a list of DOIs, deduplicating requests and caching results.

    Args:
        dois: Iterable of DOI strings.
        timeout: Per-request timeout in seconds.

    Returns:
        List of status records, one per unique DOI.
    """
    unique_dois = sorted(set(dois))
    results: List[Dict[str, Optional[str]]] = []
    cache: Dict[str, Dict[str, Optional[str]]] = {}

    for doi in unique_dois:
        if doi not in cache:
            cache[doi] = _check_doi(doi, timeout)
        results.append(cache[doi])

    return results


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Batch-verify DOIs from an econ-compass Markdown reading list or BibTeX file."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/check_dois.py -i growth-reading-list.md\n"
            "  python scripts/check_dois.py -i growth-reading-list.bib --timeout 15"
        ),
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        required=True,
        help="Path to a Markdown reading list or BibTeX file.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Timeout in seconds for each DOI resolution request (default: 10).",
    )
    args = parser.parse_args(argv)

    if not args.input.exists():
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        return 1

    dois = _extract_dois(args.input)
    if not dois:
        report = {
            "input": str(args.input),
            "total": 0,
            "valid": 0,
            "invalid": 0,
            "timeout": 0,
            "check": 0,
            "results": [],
            "message": "No DOIs found.",
        }
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    results = check_dois(dois, timeout=args.timeout)

    counts: Dict[str, int] = {
        "valid": 0,
        "invalid": 0,
        "timeout": 0,
        "check": 0,
        "error": 0,
    }
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1

    report = {
        "input": str(args.input),
        "total": len(results),
        "valid": counts.get("valid", 0),
        "invalid": counts.get("invalid", 0),
        "timeout": counts.get("timeout", 0),
        "check": counts.get("check", 0),
        "error": counts.get("error", 0),
        "results": results,
    }

    print(json.dumps(report, indent=2, ensure_ascii=False))

    all_valid = all(r["status"] == "valid" for r in results)
    return 0 if all_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
