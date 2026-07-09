# Output Template Specification

> This reference defines the exact output format for curated reading lists and PDF download results. Follow this template strictly to ensure consistency.

## Output Files

For each curated reading list, produce the following files:

1. **`[domain-name]-reading-list.md`** — Human-readable Markdown reading list (always)
2. **`[domain-name]-reading-list.bib`** — Machine-readable BibTeX file (always)
3. **`[domain-name]-reading-list-notion.csv`** — Notion-compatible database format (optional, if user mentions Notion)
4. **`[domain-name]-reading-list-obsidian.md`** — Obsidian callout format (optional, if user mentions Obsidian)
5. **`unavailable-papers.md`** — List of papers that could not be auto-downloaded (if Phase 7 triggered)

---

## Markdown Output Template

```markdown
# [Domain Name] Economics — Essential Reading List

> Curated on [YYYY-MM-DD]. N = [paper count] papers selected for foundational importance,
> methodological innovation, branch/cluster coverage, and irreplaceability.
> Selection follows the econ-compass methodology.

---

## Paper 1: [Full Title in English]

- **Authors**: [Author1 Last, First; Author2 Last, First; ...]
- **Year**: [YYYY]
- **Journal**: [Full Journal Name]
- **DOI**: [https://doi.org/XXXXX]
- **Core Branch/Cluster**: [Which branch or thematic cluster this paper represents]

### Summary
[Brief abstract in the requested output language. 3-5 sentences summarizing the research question, method, key finding, and significance.]

### Why This Paper Is Irreplaceable
[2-5 sentences explaining what unique intellectual contribution this paper made and why no other paper can substitute for it. Prioritize substance over strict brevity. Focus on: what new idea/method/evidence did it introduce? Why would removing it leave a gap?]

---

## Paper 2: [Full Title in English]

[... repeat for all N papers ...]

---

## Selection Notes

**Covered Branches/Clusters:** [List all core branches or thematic clusters covered, with paper numbers]

**Balance:**
- Theoretical: [N] | Empirical/Applied: [N] | Mixed: [N]
- Structural: [N] | Reduced-form: [N] | Experimental: [N]
- Classic (pre-2005): [N] | Contemporary (post-2010): [N] | Transitional (2005-2010): [N]

**Journal Distribution:**
| Journal (Abbreviation) | Count |
|------------------------|-------|
| [Journal 1] | [N] |
| [Journal 2] | [N] |
| ... | ... |
[Brief note on journal quality, e.g., "All papers from T5 or field-top journals."]

Use standard journal abbreviations (AER, QJE, JPE, Econometrica, RES, JDE, etc.). Group journals by their standard short name. Add a brief note on overall venue quality.

**Validation Sources:**
- Syllabi reviewed: [N] PhD programs ([list programs consulted])
- Handbook chapters consulted: [List specific chapters]
- Key review articles referenced: [List JEL/JEP articles]
- Additional sources: [e.g., citation network analysis, awards]

**Alternative Candidates Considered and Rejected:**
| Paper | Why Rejected | Replaced By |
|-------|-------------|-------------|
| [Author (Year), "Title"] | [Reason — superseded, narrower scope, less influential, overlapping contribution] | [Paper #N] |

Example of specific rejection reason:

| Paper | Why Rejected | Replaced By |
|-------|-------------|-------------|
| Card & Krueger (1994), "Minimum Wages and Employment" | Superseded by later meta-analyses; kept Dube et al. (2010) for broader geographic coverage | Paper 3 |

---

### PDF Download Results
[Appended only if Phase 7 was executed]
- Successfully downloaded: X/N
- Could not auto-download: (N-X)
- Saved to: `./pdfs/`
- Unavailable papers listed in: `unavailable-papers.md`
```

---

## BibTeX Output Template

```bibtex
% [Domain Name] Economics — Essential Reading List
% Curated on [YYYY-MM-DD]
% N = [paper count] papers

@article{key1,
  title   = {[Full Title]},
  author  = {[LastName1, FirstName1] and [LastName2, FirstName2]},
  journal = {[Full Journal Name]},
  year    = {[YYYY]},
  volume  = {[VV]},
  number  = {[NN]},
  pages   = {[PPP-PPP]},
  doi     = {[DOI without https://doi.org/ prefix]}
}

@article{key2,
  [...]
}
```

### BibTeX Key Convention
Use the format: `[FirstAuthorLastName][Year][FirstWordOfTitle]`
- Example: `acemoglu2001colonial` for Acemoglu, Johnson, Robinson (2001) "The Colonial Origins of Comparative Development"
- Example: `card1994minimum` for Card & Krueger (1994) "Minimum Wages and Employment"
- If the first word is a common stop word (the, a, an), use the second word
- Ensure all keys are unique

---

## Notion Database Format (Optional)

If the user mentions Notion, offer this format as a CSV file that can be imported into a Notion database:

```csv
#, Title, Authors, Year, Journal, DOI, Core Branch, Why Irreplaceable
1, "The Colonial Origins of Comparative Development", "Acemoglu, Daron; Johnson, Simon; Robinson, James A.", 2001, American Economic Review, https://doi.org/10.1257/aer.91.5.1369, Institutions and Development, "This paper established..."
```

---

## Obsidian Callout Format (Optional)

If the user mentions Obsidian, offer this format with callout blocks:

```markdown
# [Domain Name] — Essential Reading List

> [!important] 1. The Colonial Origins of Comparative Development
> **Authors**: Acemoglu, Daron; Johnson, Simon; Robinson, James A.
> **Year**: 2001 | **Journal**: American Economic Review
> **DOI**: https://doi.org/10.1257/aer.91.5.1369
> **Branch**: Institutions and Development
>
> **Summary**: [summary text]
>
> **Why Irreplaceable**: [2-5 sentence reasoning]

---

> [!important] 2. [...]
```

---

## Unavailable Papers Template (Phase 7)

When some papers cannot be auto-downloaded, generate a separate file. Papers that
have a DOI always receive a direct access link (DOI resolver) even when no
open-access PDF is found automatically.

```markdown
# Papers That Could Not Be Auto-Downloaded

> [Domain Name] — [YYYY-MM-DD]. The following papers from the reading list could not be automatically downloaded as published-version PDFs. A direct access link is provided for each so the user can retrieve the paper through their institutional subscription.

| # | Title | Authors | DOI | Status | Manual Link | Source Tried | Reason |
|---|-------|---------|-----|--------|-------------|--------------|--------|
| 3 | [Title] | [Authors] | [DOI] | manual_link | https://doi.org/10.xxxx/xxxxx | semanticscholar | No open-access published-version PDF found |
| 7 | [Title] | [Authors] | [DOI] | manual_link | https://doi.org/10.xxxx/xxxxx | - | DOI resolution failed — paper may not be digitized or DOI is incorrect |
| 12 | [Title] | [Authors] | - | unavailable | - | - | No DOI or access link found |

## How to use the Manual Link
- **doi_resolver**: The DOI resolver (`https://doi.org/...`) redirects to the publisher's official article page, where the PDF can be downloaded if the user's institution has a subscription.
- **landing_page**: A publisher or repository page for the article.

## Suggestions
- Open the DOI resolver link while connected to your university/library network or VPN
- If the link redirects to a paywall, request the paper through your library's interlibrary loan
- Check ResearchGate or the author's personal website only if you cannot access the publisher version
```

---

## Language Specification

The output language for **summaries** and **"Why Irreplaceable" reasoning** follows the user's prompt language.

**Default:** English (if not specified or if the user's prompt is in English).

**Chinese prompt rule:** If the user's prompt is in Chinese, output summaries and reasoning in Chinese. Paper metadata (title, authors, journal, DOI) always stays in original language (typically English).

**Always in original language (regardless of user language):**
- Paper titles
- Author names
- Journal names
- DOI
- BibTeX entries
- PDF filenames

---

## Quality Checklist

Before finalizing any reading list, verify:

- [ ] All N papers are included with complete metadata
- [ ] Every core branch (or thematic cluster) is represented by at least one paper
- [ ] DOIs are verified and functional
- [ ] BibTeX keys are unique and follow the naming convention
- [ ] Each "Why Irreplaceable" provides a genuine, specific justification (2-5 sentences; prioritize substance over brevity)
- [ ] The selection includes a mix of eras and methods
- [ ] At least 3 rejected alternatives are listed with specific reasons
- [ ] Validation sources are documented (minimum 3)
- [ ] Output language matches user's prompt language for summaries and reasoning
- [ ] If Chinese prompt, user was asked about Chinese literature inclusion
- [ ] If PDF download was requested, download results are appended
- [ ] Unavailable papers list is generated if any downloads failed
