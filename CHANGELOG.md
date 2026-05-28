# Changelog

All notable changes to Econ Compass (formerly econ-literature-curator) will be documented in this file.

---

## [2.0.1] — 2026-05-28

### 🔧 Fixed
- **S1 — Accelerated mode exception (SKILL.md Phase 1):** Added explicit rule for quick-test and pre-stated-constraint scenarios. When the user says "测试一下" / "quick test" or pre-states "无需下载", interactive questions (Chinese literature, PDF download) are now explicitly skipped with a note in the output header — eliminating the ambiguity that caused systematic test failures.
- **S2 — Phase 7 trigger clarified (SKILL.md Phase 7):** Replaced ambiguous "proactively ask" with explicit trigger rule: skip Phase 7 entirely if the user pre-stated "no download needed", otherwise ask. Distinguishes between "user already decided" and "user needs to be asked."

### 🔄 Changed
- **S3 — "Why Irreplaceable" length relaxed (3 files):** Changed from "1-3 sentences" to "2-5 sentences, prioritize substance over brevity." Updated in: SKILL.md Phase 6, SKILL.md Quality Standards, and selection-methodology.md writing guide. Resolves the consistent test finding that high-quality justifications for complex papers naturally require 3-4 sentences.
- **S4 — Journal Distribution added to Selection Notes (output-specification.md):** Added mandatory "Journal Distribution" table to the Selection Notes template. Ensures consistent journal reporting across all curated lists (previously present in some outputs and missing in others).

### 📊 Test Results (pre-fix baseline)
| Metric | Value |
|--------|-------|
| Avg pass_rate (2 evals) | 0.80 |
| Always FAIL expectations | Chinese lit question, PDF download question |
| Expectation improved by S1+S2 | +2 PASS → projected pass_rate 1.00 |
| Expectation improved by S3 | PARTIAL → PASS (format constraint now matches content reality) |
| Expectation improved by S4 | Output format consistency between test cases |

---

## [2.0.0] — 2026-05-27

### 🆕 Added
- **PDF Auto-Download (Phase 7):** Automatically downloads open-access PDFs of listed papers via Semantic Scholar, Unpaywall, arXiv, NBER, SSRN, and RePEc. Generates download summary and unavailable-papers list.
- **Arbitrary Domain Support:** Now handles any economics-related domain — from broad subfields to narrow research topics ("digitalization and firm innovation," "carbon pricing"). Uses thematic clustering for non-predefined domains.
- **Chinese Language Support:** Chinese prompts trigger Chinese-language summaries and reasoning. Automatically offers to include Chinese-language literature (《经济研究》《管理世界》等).
- **Cross-Discipline Support:** Added finance, econometrics, complex economics, and 30+ additional subfields with tailored selection criteria weights.
- **Notion and Obsidian Output Formats:** Optional alternative output formats for popular note-taking tools.
- **Semantic Scholar API Integration:** Used for citation verification and open-access PDF detection.
- **New Reference Files:** `pdf-download-guide.md`, expanded `field-taxonomy.md` (47+ subfields), expanded `journal-tiers.md` (100+ journals with ABS/FT50/UTD24/SSCI classifications + Chinese top 10).
- **Supporting Files:** `CONTRIBUTING.md`, `CHANGELOG.md`, `evals/evals.json`.

### 🔄 Changed
- **Brand Rename:** `econ-literature-curator` → `econ-compass` (🧭)
- **Selection Methodology:** "Why Irreplaceable" reasoning shortened from long paragraphs to 1-3 concise sentences.
- **Field Taxonomy:** Expanded from 15 to 47+ subfields across 12 major categories, based on the Handbook of Economics series.
- **Journal Tiers:** Massively expanded to include UTD24, FT50, ABS 3/4/4*, SSCI Q1 classifications, finance Top 3 (JF, JFE, RFS), and Chinese top 10 journals.
- **Quality Standards:** Extended from 6 to 12 checklist items, including PDF download completeness.
- **SKILL.md:** Restructured from 6 phases to 7 phases (added Phase 7: PDF Download). Now under 350 lines with detail delegated to reference files.

### 🔧 Fixed
- **Domain Coverage Strategy:** Non-matched domains now use thematic clustering instead of being rejected. Predefined taxonomy is a guide, not a constraint.
- **Cross-Discipline Standards:** Each discipline now has documented criterion weight adjustments (finance: higher empirical significance; econometrics: higher methodological innovation; complex economics: higher paradigm creation).

### 📊 File Changes
```
Files changed:    9 (of 7 original)
Additions:        +3,200 lines
File growth:      850 → ~4,000 lines total
New files:        CONTRIBUTING.md, CHANGELOG.md, evals/evals.json, references/pdf-download-guide.md
```

---

## [1.0.0] — Initial Release (as econ-literature-curator)

### Features
- Five-dimension paper selection criteria (Foundational, Methodological, Empirical, Branch Coverage, Irreplaceability)
- 15 predefined economics subfields with core branches
- Three-tier journal classification (T5, General Field Tops, Subfield Tops)
- Six-phase curation workflow
- Markdown + BibTeX output with detailed "Why Irreplaceable" reasoning
- Multi-language output support (summaries in user's language)
- MIT License
