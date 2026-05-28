# PDF Download Guide

> Load this reference only when the user has confirmed they want to download PDFs (Phase 7). This guide provides step-by-step instructions for attempting to download each paper in the curated reading list.

## Strategy Overview

The goal is to download as many papers as possible using legitimate, publicly accessible channels. Attempt each paper in order, trying multiple approaches before giving up on any single paper.

**Priority of approaches (try in this order):**

1. **Semantic Scholar Open Access PDF** — Check if Semantic Scholar has an open-access PDF link for the DOI
2. **Unpaywall API** — Query Unpaywall for legal open-access versions (preprints, accepted manuscripts, published versions)
3. **arXiv / SSRN / NBER / RePEc** — Check preprint repositories for freely available versions
4. **Direct DOI resolution** — Attempt to resolve the DOI to a PDF directly
5. **Report as unavailable** — If all approaches fail, add the paper to the unavailable list

---

## Download Workflow (Execute for Each Paper in Sequence)

### Step 1: Semantic Scholar Lookup

For each paper's DOI, query the Semantic Scholar API:

```
GET https://api.semanticscholar.org/graph/v1/paper/DOI:{DOI}?fields=title,openAccessPdf
```

If the response includes `openAccessPdf.url`, download the PDF from that URL.

### Step 2: Unpaywall API

If Semantic Scholar does not provide an open-access PDF, query Unpaywall:

```
GET https://api.unpaywall.org/v2/{DOI}?email=your-email@example.com
```

If the response includes `best_oa_location.url_for_pdf`, download from that URL.

Unpaywall distinguishes between:
- **Published version** (gold OA, hybrid)
- **Accepted manuscript** (green OA, post-print)
- **Submitted manuscript** (green OA, pre-print)

Prefer published version first, then accepted manuscript, then submitted manuscript.

### Step 3: Preprint Repository Search

For economics papers, check these repositories:
- **NBER Working Papers**: Many seminal economics papers exist as NBER working papers (freely available at nber.org/papers/w{number})
- **SSRN**: Search ssrn.com for the paper title — many authors upload preprints
- **arXiv**: Particularly useful for econometrics, quantitative finance (q-fin), and computational economics (econ.GN, econ.EM, econ.TH)
- **RePEc / IDEAS**: Check ideas.repec.org for working paper versions
- **IZA Discussion Papers**: Free access to IZA working papers

### Step 4: Direct DOI Resolution

If all API and repository checks fail, attempt direct resolution:

```
https://doi.org/{DOI}
```

Follow redirects. Some publishers provide free access to specific articles. If the final URL is a publisher page with a PDF link accessible without authentication, download it.

### Step 5: Mark as Unavailable

If all four steps fail, add the paper to the unavailable papers list with the specific reason:
- "Paywalled — no open-access version found"
- "DOI resolution failed"
- "Publisher blocks automated access"
- "Paper not digitized / too old"

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
[01/15] ✅ Downloaded: "The Colonial Origins..."
[02/15] ✅ Downloaded: "Unified Growth Theory..."
[03/15] ❌ Failed: Paywalled, no OA version via Unpaywall
[04/15] ✅ Downloaded: "Minimum Wages and Employment..."
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
| ✅ Successfully downloaded | X/N |
| ❌ Could not auto-download | (N-X)/(N) |

**Saved to:** `./pdfs/`

| # | Title | Status | Source |
|---|-------|--------|--------|
| 1 | [Title] | ✅ | Semantic Scholar OA |
| 2 | [Title] | ✅ | Unpaywall (gold OA) |
| 3 | [Title] | ❌ | Paywalled — see unavailable-papers.md |
| ... | ... | ... | ... |

Papers that could not be downloaded are listed in `unavailable-papers.md`.
```

---

## Rate Limiting and Ethics

- Respect API rate limits: Semantic Scholar allows ~100 requests per 5 minutes without an API key
- Unpaywall requires an email for identification — use a generic project email
- Do not attempt to bypass publisher paywalls or use Sci-Hub — this skill uses only legal open-access channels
- If a paper is behind a paywall and has no OA version, honestly report it as unavailable
- The goal is convenience, not piracy — the user can always access paywalled papers through their institutional library

---

## Notes for the Future

This guide is designed to be updated as new open-access tools and APIs become available. If you discover a better PDF retrieval tool on GitHub (especially one specifically designed for economics), update this guide to reference it. All external tool references should be documented in the README's Acknowledgments section.
