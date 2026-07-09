# Changelog

All notable changes to Econ Compass (formerly econ-literature-curator) will be documented in this file.

---

## [2.2.1] - 2026-07-09

### Fixed
- Hardened BibTeX generation, validation, format checking, and grading so paper-count mismatches are detected and penalized consistently.
- Tightened PDF download behavior for published-version retrieval, working-paper/preprint filtering, arXiv query encoding, filename generation, and report output paths.
- Synchronized benchmark scoring, schemas, runner behavior, aggregation output, and README commands for a 100-point rubric.
- Made maintenance scripts safer for public clones by avoiding default task overwrites and reporting missing private gold clearly.
- Updated templates and legacy evals from older short-justification wording to the current 2-5 sentence standard; saved eval JSON as UTF-8 without BOM.

---

## [2.2.0] — 2026-07-08

### 🆕 Added
- **Open-source readiness pass:** Added `benchmark/reports/`, `.env`, and virtual-environment directories to `.gitignore`; removed generated reports and `__pycache__` from the working tree; switched PDF-download reports to relative POSIX paths so local absolute paths are not leaked.
- **Bundled engineering tools (`scripts/`):** Real, executable helpers that go beyond prompt instructions.
  - `generate_bibtex.py` — generate canonical BibTeX from a Markdown reading list.
  - `validate_output.py` — programmatically verify compliance with `references/output-specification.md`.
  - `check_dois.py` — batch-verify DOIs via `doi.org`.
  - `download_pdfs.py` — download published-version open-access PDFs via a multi-source fallback chain (Unpaywall → Semantic Scholar → OpenAlex → arXiv); skips preprints/working papers and provides DOI resolver links for manual retrieval.
  - Output templates in `assets/` for reading lists and selection notes.
- **SKILL.md quality gates:** Added `When NOT to Use This Skill`, `Exclusion Rules`, `Branch Prioritization for Small N`, mandatory `Validation Sources`, specific `Alternative Candidates` requirements, and a `Bundled Tools` reference section.
- **Benchmark expansion:** Extended from 15 to 20 test cases (E016–E020) covering file-dependent syllabus comparison, Chinese economic transformation with Chinese literature, behavioral-economics original-research-only, reduced-form microeconometrics, and narrow teacher value-added topics. Added paraphrase variants for E001, E002, and E006.
- **Enhanced grading:** `grade_output.py` now checks Validation Sources depth and Alternative Candidates specificity; `format_checker.py` handles CRLF line endings and avoids spanning empty metadata fields across lines.
- **PDF download benchmark:** Added `benchmark/scripts/test_pdf_download.py` and `benchmark/public/fixtures/pdf-download-fixture.md`. Measures published-version OA PDF auto-download success rate for a 10-paper canonical list; supports live API queries and deterministic mock mode; reports per-paper status, source, version, and a direct manual link when auto-download is not possible.
- **Bug fix:** `scripts/download_pdfs.py` now correctly extracts papers from econ-compass Markdown outputs that use `## Paper N:` headings (it previously only recognized horizontal-rule separators).

### 📊 Benchmark Results (simulate mode, 3 iterations, 20 tasks)
| Metric | Value |
|--------|-------|
| with_skill mean | 91.14 |
| without_skill mean | 53.86 |
| Delta | +37.29 |
| Quality gate | **PASS** |

> Note: `simulate` mode generates synthetic outputs to validate the scoring pipeline. Run `live` mode against a real LLM executor for production evaluation.

---

## [2.1.0] — 2026-07-08

### 🆕 Added
- **Comprehensive benchmark suite (`benchmark/`):** Added a full evaluation framework inspired by SWE-bench, GAIA, and Skill-Creator eval practices.
  - 15 stratified test cases covering predefined subfields, thematic topics, cross-discipline requests, small/large N, Chinese/English prompts, and near-miss negative tests.
  - Sealed private gold standard (`benchmark/private-gold/gold.json`) with must-find papers, acceptable alternatives, and forbidden decoys.
  - Anti-cheat mechanisms: canary strings, public-tasks/private-gold split, critical caps, and with_skill vs without_skill delta scoring.
  - Automated grading scripts: `format_checker.py`, `grade_output.py`, `aggregate_results.py`, `leak_check.py`, and `run_benchmark.py`.
  - Quality gate: with_skill ≥ 80, without_skill ≤ 65, delta ≥ +15, flaky rate < 15%.

### 📊 Benchmark Results (simulate mode, 3 iterations)
| Metric | Value |
|--------|-------|
| with_skill mean | 91.31 |
| without_skill mean | 55.37 |
| Delta | +35.94 |
| Quality gate | **PASS** |

> Note: `simulate` mode generates synthetic outputs to validate the scoring pipeline. Run `live` mode against a real LLM executor for production evaluation.

---

## [2.0.1] — 2026-05-28

### 🔧 Fixed
- **S1 — Accelerated mode exception (SKILL.md Phase 1):** Added explicit rule for quick-test and pre-stated-constraint scenarios. When the user says "测试一下" / "quick test" or pre-states "无需下载", interactive questions (Chinese literature, PDF download) are now explicitly skipped with a note in the output header — eliminating the ambiguity that caused systematic test failures.
- **S2 — Phase 7 trigger clarified (SKILL.md Phase 7):** Replaced ambiguous "proactively ask" with explicit trigger rule: skip Phase 7 entirely if the user pre-stated "no download needed", otherwise ask. Distinguishes between "user already decided" and "user needs to be asked."

### 🔄 Changed
- **S3 — "Why Irreplaceable" length relaxed (3 files):** Changed the older short-justification wording to "2-5 sentences, prioritize substance over brevity." Updated in: SKILL.md Phase 6, SKILL.md Quality Standards, and selection-methodology.md writing guide. Resolves the consistent test finding that high-quality justifications for complex papers naturally require 3-4 sentences.
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
- **Selection Methodology:** "Why Irreplaceable" reasoning standardized to 2-5 substantive sentences, prioritizing specificity over artificial brevity.
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
