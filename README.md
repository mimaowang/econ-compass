# 🧭 Econ Compass

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Skills](https://img.shields.io/badge/Skills-Compatible-green.svg)](https://skills.sh)

> **Your compass for navigating economics literature.**
> Find the most important papers in any field — in minutes, with one-click PDF downloads.

Help you quickly gain a deep understanding of any subfield of economics. A rigorous, multi-dimensional skill for curating essential reading lists in any economics field, subfield, or research topic — and automatically downloading the PDFs. Built on the intellectual tradition of PhD field exams, this skill identifies genuinely **canonical** papers (not just highly cited ones) and explains *why* each paper is irreplaceable.

---

## 🎯 What This Skill Does

### 📚 Smart Curation (Function A)

Given any economics-related domain and a paper count N (default 15), this skill produces:

1. **A curated Markdown reading list** — N papers with full metadata, summaries in your language, and 1-3 sentence explanations of why each paper is irreplaceable
2. **A BibTeX file** — Import directly into Zotero, Mendeley, or any reference manager
3. **Selection documentation** — Branch/cluster coverage analysis, methodological balance, and rejected alternatives with specific reasons
4. **Optional Notion/Obsidian formats** — Ready-to-import formats for your note-taking tools

The output is not a "top-N by citations" list. It is a **curriculum** — a reading list designed to give you systematic understanding of a field with the fewest possible papers.

### 📥 Auto PDF Download (Function B)

After generating the reading list, Econ Compass offers to download all the papers as PDFs:

- Attempts to find legal open-access versions via Semantic Scholar, Unpaywall, arXiv, NBER, SSRN, and RePEc
- Names each PDF with the paper number, title, and authors for easy organization
- Reports which papers could not be auto-downloaded in a separate file
- Respects publisher paywalls — only downloads freely available versions

---

## 🔬 The Selection Methodology

This skill applies **five dimensions of selection**:

| Dimension | Question | Weight |
|-----------|----------|--------|
| **Foundational Contribution** | Did this paper create or reshape a research program? | Highest |
| **Methodological Innovation** | Did it introduce a new identification strategy, framework, or measurement? | High |
| **Empirical Significance** | Is the finding economically meaningful and robust? | Medium |
| **Branch / Cluster Coverage** | Does the set collectively cover all major areas of the field? | Essential for Set |
| **Irreplaceability** | Would removing this paper leave a gap no other paper fills? | Decisive |

**Validation sources**, in order of authority:
1. PhD field course syllabi from top-20 economics departments
2. Handbook of Economics chapters (Elsevier series)
3. JEL and JEP review articles — authoritative surveys by leading scholars
4. Citation network centrality (supporting, never primary)

**Cross-discipline adjustments:**
- **Finance:** Higher weight on empirical significance — major discoveries (Fama-French factors, IPO anomalies) can be foundational without methodological novelty
- **Econometrics:** Higher weight on methodological innovation — a new estimator is its own classic
- **Complex/Agent-Based Economics:** Higher weight on paradigm creation — introducing a new modeling approach outweighs single empirical findings

---

## 📦 Installation

```bash
npx skills add econ-compass
```

Or install manually by cloning this repository into your skills directory.

---

## 🚀 Quick Start

### English

```
"Find the 10 most important papers in development economics."
```

```
"I need to understand the economics of digitalization and firm innovation. Give me 8 essential papers."
```

```
"Curate the foundational literature on asset pricing. Focus on post-1990 work."
```

### 中文（Chinese）

```
"帮我找 15 篇劳动经济学最重要的论文，我需要快速了解这个领域。"
```

```
"我想快速了解碳定价的经济学研究，给我推荐 8 篇经典文献。"
```

```
"金融计量学有哪些必读论文？推荐 10 篇。"
```

### What Happens Next

The skill will:
1. Confirm the domain, paper count, and any special constraints
2. (If Chinese prompt) Ask whether to include Chinese-language literature
3. Map the field's core branches or thematic clusters
4. Identify canonical papers using the five-dimension criteria
5. Apply the irreplaceability filter
6. Produce Markdown + BibTeX output with full justifications
7. **Ask if you want to download the PDFs**

---

## 🗂 Supported Domains

Econ Compass covers **47+ economics-related fields**, organized into 12 major categories:

| Category | Fields Covered |
|----------|---------------|
| **Micro Theory & Methods** | Micro Theory, Game Theory, Macroeconomics, Monetary, Growth, Econometrics, Math & Computational Economics |
| **Applied Micro: Labor, Public & Social** | Labor, Public, Health, Education, Population & Family, Law & Economics, Economics of Crime |
| **Spatial & Regional** | Urban & Regional, Real Estate & Transport |
| **IO & Innovation** | Industrial Organization, Innovation, Digitization & Platforms |
| **International** | International Trade, International Finance / Open Macro |
| **Development & Agriculture** | Development, Agricultural |
| **Environmental & Resources** | Environmental, Energy, Climate Change, Natural Resources |
| **Behavioral & Experimental** | Behavioral, Experimental |
| **Political Economy & History** | Political Economy, Economic History, Institutional |
| **Finance** | Asset Pricing, Corporate Finance, Banking & Intermediation, Market Microstructure, Household Finance, Insurance & Risk |
| **Culture & Special Topics** | Cultural, Media, Sports, Defense |
| **Income & Welfare** | Inequality, Social Choice & Welfare, Social Networks, Religion, Philanthropy & Nonprofits |

**Not listed? No problem.** Econ Compass also handles narrow or emerging topics (like "digitalization and firm innovation" or "carbon pricing") by using thematic clustering instead of predefined branches. The taxonomy is a guide, not a cage.

Full taxonomy with all core branches in `references/field-taxonomy.md`.

---

## 📝 Output Example

### Markdown Output (excerpt)

```markdown
# Development Economics — Essential Reading List

> Curated on 2026-05-27. N = 10 papers selected for foundational importance.

---

## Paper 1: The Colonial Origins of Comparative Development

- **Authors**: Acemoglu, Daron; Johnson, Simon; Robinson, James A.
- **Year**: 2001
- **Journal**: American Economic Review
- **DOI**: https://doi.org/10.1257/aer.91.5.1369
- **Core Branch**: Institutions and Governance

### Summary
Using European settler mortality as an instrument for institutional quality, Acemoglu,
Johnson, and Robinson show that institutions — not geography or culture — are the
fundamental cause of differences in economic development across former colonies.

### Why This Paper Is Irreplaceable
This paper established the empirical case that institutions cause development — not
the reverse — using a creative instrumental variable strategy (settler mortality)
that has been replicated and debated across dozens of subsequent studies. It turned the
institutions hypothesis from a theoretical conjecture into an empirically testable claim,
fundamentally reorienting development economics toward the study of institutional origins.
```

### BibTeX Output (excerpt)

```bibtex
@article{acemoglu2001colonial,
  title   = {The Colonial Origins of Comparative Development: An Empirical Investigation},
  author  = {Acemoglu, Daron and Johnson, Simon and Robinson, James A.},
  journal = {American Economic Review},
  year    = {2001},
  volume  = {91},
  number  = {5},
  pages   = {1369--1401},
  doi     = {10.1257/aer.91.5.1369}
}
```

---

## 🌐 Language Support

| User Prompt Language | Summary & Reasoning Language | Paper Metadata | Chinese Lit Option |
|---|---|---|---|
| English | English | Original (English) | Not offered |
| Chinese (中文) | Chinese (中文) | Original (English) | Offered: "是否需要同时检索中文文献？" |
| Other languages | Follows prompt language | Original (English) | Not offered |

**Chinese literature opt-in:** When triggered (Chinese prompt only), the skill will ask whether to include papers from top Chinese journals like 《经济研究》, 《管理世界》, 《经济学（季刊）》, etc. See `references/journal-tiers.md` for the full Chinese top-10 list.

---

## 🎓 Why This Skill Exists

**The problem:** A graduate student or researcher entering a new economics field faces thousands of papers. Generic search tools return the most-cited papers — but citation counts are biased toward convenience references, survey papers, and chronologically old work. Many truly canonical papers are not the most cited. And even after finding the right papers, downloading them one by one wastes hours.

**The solution:** Econ Compass emulates the judgment of an experienced field committee member — selecting not by algorithm but by asking: *"If this paper did not exist, would the field be materially different?"* Then it downloads everything for you.

The selection method is:
- **Transparent** — Every inclusion is justified with specific reasoning
- **Reproducible** — Selection criteria are documented and auditable
- **Efficient** — From "I know nothing about this field" to "I have the essential papers + PDFs" in minutes
- **Curriculum-oriented** — The output is a course of study, not a bibliography

---

## 📊 Journal Coverage

Econ Compass covers the full journal landscape:
- **Tier 1:** Top Five (AER, QJE, JPE, EMA, RES)
- **Tier 2:** Major general interest journals (AEJ series, REStat, JEEA, EJ, JEL, JEP, etc.)
- **Tier 3:** Subfield-specific field tops (60+ journals across all fields)
- **Tier 4:** Finance Top 3 (JF, JFE, RFS) and UTD24/FT50 crossover journals
- **Appendix:** Top 10 Chinese economics journals

All aligned with **ABS 3/4/4***, **FT50**, **UTD24**, and **SSCI Q1** classifications. Full list in `references/journal-tiers.md`.

---

## 🤝 Contributing

Contributions are welcome! Ways to contribute:

- **Suggest a paper**: Open an issue with the paper, the field/branch it covers, and why it should replace an existing selection
- **Improve the taxonomy**: Propose additions or refinements to `field-taxonomy.md`
- **Improve the journal tiers**: Suggest updates to `journal-tiers.md`
- **Share a syllabus**: Help validate the methodology by sharing anonymized PhD field course syllabi
- **Report errors**: Incorrect DOIs, metadata, or factual errors in selection reasoning

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 📜 Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

---

## 📄 Acknowledgments

This skill was developed using the [Anthropic Skill Creator](https://github.com/anthropics/skills) methodology and follows its best practices for skill architecture, progressive disclosure, and evaluation.

The field taxonomy and subfield classifications are guided by the **Handbook of Economics** series (Elsevier), which provides the authoritative reference framework for economics subfields. All taxonomy entries represent original synthesis and curation, not direct reproduction of copyrighted content.

**APIs and services used:**
- [Semantic Scholar API](https://api.semanticscholar.org/) — citation verification and open-access paper identification (non-commercial use)
- [Unpaywall API](https://unpaywall.org/) — legal open-access paper retrieval (free tier, requires email identification)

**Academic traditions informing the selection methodology:**
- Economics PhD field exam traditions at MIT, Harvard, Chicago, Stanford, Berkeley, LSE, and other leading departments
- Journal of Economic Literature (JEL) classification system — as a reference for field boundaries

All paper summaries and "Why Irreplaceable" analyses are original work. Paper metadata (titles, authors, DOIs) are factual public information. This project is independent and not affiliated with any of the organizations listed above.

---

## ⚠️ Disclaimer

This skill provides curated recommendations based on established academic consensus. It is not a substitute for:
- Reading the papers yourself and forming your own judgment
- Consulting with your advisor or field committee
- Conducting a systematic literature review for original research

Selection reflects the judgment embedded in the skill's methodology and the state of academic consensus at the time of curation. Economics is a living discipline — canonical status evolves over time.

**PDF downloads are limited to legally available open-access versions. This skill does not bypass publisher paywalls. Users should access paywalled papers through their institutional library subscriptions.**

---

**Built for the economics research community. If this skill helps you, please ⭐ the repository!**

**[mimaowang](https://github.com/mimaowang) · MIT License · [Changelog](CHANGELOG.md)**
