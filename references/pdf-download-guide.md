# PDF Download Guide

> Load this reference only when the user has confirmed they want to download PDFs (Phase 7). This guide provides step-by-step instructions for attempting to download each paper in the curated reading list.

## Strategy Overview

The goal is to retrieve the **published-journal version** of each paper through legitimate, publicly accessible channels. Preprints, accepted manuscripts, and working-paper versions are **not** substituted for the published article.

**Priority of approaches (try in this order):**

1. **Unpaywall API** — Query Unpaywall for the best legal open-access location and inspect `best_oa_location.version`
2. **Semantic Scholar Open Access PDF** — Check if Semantic Scholar has an open-access PDF link for the DOI
3. **OpenAlex API** — Query OpenAlex for the best open-access PDF URL and version
4. **arXiv** — Search by title + first author; treat any match as a preprint (do **not** substitute for the published version)
5. **Direct DOI resolver link** — If no published-version OA PDF is found automatically, provide the DOI resolver link (`https://doi.org/{DOI}`) so the user can retrieve the paper through their institutional subscription
6. **Report as unavailable** — If no DOI or access link can be determined, add the paper to the unavailable list

---

## Version Policy

Only the following versions may be kept as an automatic download:

- **publishedVersion** — the final published journal article (gold or hybrid OA)
- **unknown** — when the source does not tag the version, but the URL points to a publisher/repository rather than a preprint server

The following versions are **deliberately skipped** and reported as `manual_link`:

- **acceptedVersion** / **submittedVersion** — green-OA manuscripts
- **preprint** — arXiv, SSRN, NBER, RePEc, IDEAS, or other working-paper versions

This ensures the downloaded PDF matches the cited journal article and prevents a working-paper version from silently replacing the published version.

---

## Download Workflow (Execute for Each Paper in Sequence)

### Step 1: Unpaywall API

For each paper's DOI, query Unpaywall:

```
GET https://api.unpaywall.org/v2/{DOI}?email=your-email@example.com
```

Check `best_oa_location`:

- If `version` is `publishedVersion` and `url_for_pdf` exists, download from that URL
- If `version` is `acceptedVersion` or `submittedVersion`, do **not** download automatically
- Record `url_for_landing_page` or `url` as a candidate manual link

### Step 2: Semantic Scholar

If Unpaywall does not yield a published-version PDF, query Semantic Scholar:

```
GET https://api.semanticscholar.org/graph/v1/paper/DOI:{DOI}?fields=openAccessPdf,url
```

- If `openAccessPdf.url` exists and the host is **not** a known preprint server (arXiv, bioRxiv, medRxiv, SSRN), download from that URL
- If the URL points to a preprint server, skip it and record the paper URL (`url`) as a candidate manual link

### Step 3: OpenAlex API

If Semantic Scholar does not help, query OpenAlex:

```
GET https://api.openalex.org/works/doi:{DOI}
```

- Inspect `best_oa_location.version` and `best_oa_location.pdf_url`
- Download only if the version is `publishedVersion` (or unknown and not a preprint server)
- Record `best_oa_location.landing_page_url` or `primary_location.landing_page_url` as a candidate manual link

### Step 4: arXiv Search

If the paper has no DOI or no OA PDF was found via the DOI-based sources, search arXiv by title + first author:

```
GET https://export.arxiv.org/api/query?search_query=ti:"..."+AND+au:"..."
```

Any arXiv match is a **preprint**. Do **not** substitute it for the published version. Record the arXiv abstract page as a candidate manual link only.

### Step 5: Provide a Direct Manual Link

If no published-version OA PDF was found automatically, provide the user with the most reliable direct access link, in this priority:

1. **DOI resolver** (`https://doi.org/{DOI}`) — redirects to the publisher's official article page; the user can download the PDF if their institution has a subscription
2. **Publisher landing page** from Unpaywall, Semantic Scholar, or OpenAlex
3. **arXiv/SSRN abstract page** — only if no publisher link exists

### Step 6: Mark as Unavailable

If no DOI and no access link can be determined, add the paper to the unavailable papers list with the specific reason:

- "Paywalled — no open-access version found"
- "DOI resolution failed"
- "Publisher blocks automated access"
- "Paper not digitized / too old"
- "No DOI or access link found"

---

## Naming Convention

Each downloaded PDF must be named:

```
[NN] Full Title - Authors.pdf
```

Where:

- **NN** = two-digit paper number (01, 02, ..., 15) matching the reading list order
- **Full Title** = the complete paper title (replace characters illegal in filenames: `:`, `/`, `\`, `?`, `*`, `<`, `>`, `|`, `"` with spaces)
- **Authors** = last names of first two authors (if more than 2, use "FirstAuthor et al.")

**Examples:**

- `01 The Colonial Origins of Comparative Development - Acemoglu, Johnson, Robinson.pdf`
- `04 Minimum Wages and Employment - Card, Krueger.pdf`
- `08 The Impact of Trade on Intra-Industry Reallocations - Melitz.pdf`

---

## Progress Tracking

While downloading, maintain a running tally:

```
Downloading PDFs for [Domain Name] reading list:
[01/15] ✅ Downloaded (published version): "The Colonial Origins..."
[02/15] ✅ Downloaded (published version): "Unified Growth Theory..."
[03/15] 🔗 Manual link: No published-version OA found; DOI resolver provided
[04/15] ⚠️  Skipped preprint: arXiv match ignored; DOI resolver provided
[05/15] ✅ Downloaded (published version): "Minimum Wages and Employment..."
...
```

---

## Final Summary

After processing all papers, append the download summary to the reading list Markdown file:

```markdown
---

### 📥 PDF Download Results

| Status | Count |
|--------|-------|
| ✅ Successfully downloaded (published version) | X/N |
| 🔗 Manual link provided | Y/N |
| ❌ Unavailable | Z/N |

**Saved to:** `./pdfs/`

| # | Title | Status | Source | Version | Manual Link |
|---|-------|--------|--------|---------|-------------|
| 1 | [Title] | ✅ | Unpaywall (gold OA) | publishedVersion | - |
| 2 | [Title] | ✅ | Semantic Scholar OA | publishedVersion | - |
| 3 | [Title] | 🔗 | - | - | https://doi.org/10.xxxx/xxxxx |
| ... | ... | ... | ... | ... | ... |

Papers that could not be auto-downloaded are listed in `unavailable-papers.md` with direct access links.
```

---

## Unavailable Papers Report Format

For each paper that could not be auto-downloaded, generate a row in `unavailable-papers.md`:

```markdown
| # | Title | Authors | DOI | Status | Manual Link | Source Tried | Reason |
|---|-------|---------|-----|--------|-------------|--------------|--------|
| 3 | [Title] | [Authors] | [DOI] | manual_link | https://doi.org/... | semanticscholar | No open-access published-version PDF found |
| 7 | [Title] | [Authors] | [DOI] | manual_link | https://doi.org/... | - | DOI resolution failed |
| 12 | [Title] | [Authors] | - | unavailable | - | - | No DOI or access link found |
```

---

## Rate Limiting and Ethics

- Respect API rate limits: Semantic Scholar allows ~100 requests per 5 minutes without an API key
- Unpaywall requires an email for identification — use a generic project email
- OpenAlex does not require an email but appreciates polite usage
- Do not attempt to bypass publisher paywalls or use Sci-Hub — this skill uses only legal open-access channels
- If a paper is behind a paywall and has no OA version, honestly report it and provide the DOI resolver link
- The goal is convenience and version accuracy, not piracy — the user can access paywalled papers through their institutional library

---

## Notes for the Future

This guide is designed to be updated as new open-access tools and APIs become available. If you discover a better PDF retrieval tool on GitHub (especially one specifically designed for economics), update this guide to reference it. All external tool references should be documented in the README's Acknowledgments section.
