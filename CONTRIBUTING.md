# Contributing to Econ Compass

Thank you for your interest in contributing! Econ Compass is built for and by the economics research community. Here is how you can help.

## Ways to Contribute

### 📄 Suggest a Paper

If you believe a paper should be added to (or removed from) a field's essential reading list:

1. **Open an issue** with the title: `[Paper Suggestion] [Field Name] — "Paper Title" (Author, Year)`
2. Include:
   - Full citation (authors, year, title, journal, DOI)
   - Which branch or thematic cluster it covers
   - Why it should be added (or which existing paper it should replace)
   - Your reasoning using the five-dimension framework (foundational? methodological? empirical? coverage? irreplaceable?)

### 🗂 Improve the Taxonomy

If you notice a missing branch in `references/field-taxonomy.md` or a new subfield that should be added:

1. **Open an issue** with the title: `[Taxonomy] Add/Modify [Field Name]`
2. Propose the change with:
   - Core branches to add/modify
   - Key handbooks or review articles supporting the taxonomy
   - Any papers that exemplify the new branch

### 📊 Update Journal Tiers

If you notice missing journals or incorrect tier classifications in `references/journal-tiers.md`:

1. **Open an issue** with `[Journal Tiers]`
2. Provide the journal name, proposed tier, and justification (ABS rating, SSCI quartile, field consensus)

### 🎓 Share a Syllabus

Help validate the methodology:

1. **Open an issue** with `[Syllabus] [Field Name] — [University]`
2. Share the reading list from a PhD field course (anonymized — no instructor names needed)
3. We will cross-reference it against our curated lists to improve coverage

### 🐛 Report Errors

- **Incorrect DOI or metadata**: `[Bug] Incorrect metadata for Paper #N in [Field Name] list`
- **Broken BibTeX entry**: `[Bug] BibTeX error in [Field Name].bib`
- **Missing or broken reference**: `[Bug] Reference file issue in [filename].md`
- **PDF download failure**: `[Bug] PDF download failed for [Paper Title] — DOI: [DOI]`

### 🌐 Improve Translations

If you notice Chinese-language output that could be improved:
- `[Translation] [Field Name] — [specific issue]`

---

## Contribution Process

1. **Fork** the repository
2. **Create a branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes**:
   - For taxonomy changes, edit `references/field-taxonomy.md`
   - For journal changes, edit `references/journal-tiers.md`
   - For methodology changes, edit `references/selection-methodology.md`
   - For output format changes, edit `references/output-specification.md`
4. **Test your changes**: Run the skill on a test query to verify it still produces quality output
5. **Commit** with a descriptive message: `git commit -m "Add [description]"`
6. **Push** and open a **Pull Request**

---

## Guidelines

- **Respect the methodology**: Changes to `selection-methodology.md` should preserve the five-dimension framework. If you want to change the core methodology, open an issue first to discuss.
- **Be specific**: Vague suggestions ("add more labor papers") are less helpful than specific ones ("add Card & Krueger 1994 to cover the natural experiment methodology branch")
- **Provide evidence**: When suggesting a paper, cite syllabi, handbook chapters, or review articles that support its canonical status
- **Be constructive**: This is a community project. Assume good faith and focus on making the skill better for everyone.

---

## Code of Conduct

- Be respectful and constructive
- Focus on the economics, not the personalities
- Remember: the goal is to help graduate students and researchers navigate economics literature

---

**Thank you for contributing to Econ Compass!**
