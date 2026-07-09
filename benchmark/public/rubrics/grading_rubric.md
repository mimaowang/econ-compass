# Econ Compass Grading Rubric

This rubric is used by `grade_output.py` and by human/LLM graders to score a single output. The grader receives the public task, the model output, and the private gold standard.

## Coverage (0–20)

- **20**: Every required branch/cluster is represented by at least one paper.
- **15–17**: One minor branch missing or weakly represented.
- **10–14**: Two or more branches missing; list is lopsided.
- **5–9**: Only a minority of branches covered.
- **0–4**: Coverage is essentially random or missing.

## Canonical Quality (0–25)

Scored against the private gold standard and forbidden decoy list.

- **23–25**: All or nearly all papers are canonical anchors; no forbidden decoys; excellent balance of classic and modern.
- **18–22**: Most papers are canonical; may include one acceptable alternative instead of gold anchor.
- **13–17**: Mix of canonical and merely famous/highly-cited papers; may miss 1–2 gold anchors.
- **8–12**: Several papers are popular but not irreplaceable; may include a decoy.
- **0–7**: Mostly convenience citations, surveys, or off-topic papers.

## Justification Quality (0–20)

Applies to each paper's "Why This Paper Is Irreplaceable" section.

- **18–20**: Each justification is specific, explains the unique contribution, and cites why no substitute exists. No generic praise.
- **14–17**: Mostly specific; a few lapse into generic language.
- **10–13**: Some specifics, but several are formulaic ("important and highly cited").
- **5–9**: Mostly generic or method-only descriptions.
- **0–4**: Missing, nonsensical, or copied from summaries.

## Evidence & Metadata (0–10)

- **10**: All papers have complete, accurate title / authors / year / journal / DOI.
- **8–9**: Minor inaccuracies (formatting, one missing DOI).
- **5–7**: Several missing or questionable metadata entries.
- **0–4**: Widespread missing or fabricated metadata.

## Output Format (0–10)

- **10**: Markdown + BibTeX fully conform to templates; language matches prompt; file naming correct.
- **8–9**: Minor format deviations; BibTeX mostly valid.
- **5–7**: Major format deviations or missing files.
- **0–4**: Output is unparseable or in wrong language.

### Selection Notes & Validation Sources

Selection Notes must contain a **Validation Sources** subsection listing the syllabi, handbooks, review articles, or canonical reading lists used to anchor the curation. The grader checks:

- **Validation Sources heading present**: the subsection is explicitly titled "Validation Sources" (or equivalent in the output language).
- **At least 3 distinct sources**: counted as bullet/numbered items under the subsection.

If either check fails, **Output Format is reduced by 1 point**.

### Alternative Candidates Quality

The Alternative Candidates section must be more than a placeholder. The grader checks:

- **At least 3 rows**: each row names a specific paper that was considered and rejected.
- **Specific rejection reasons**: reasons must explain *why* the candidate was set aside (e.g., overlaps with an already-selected paper, weaker identification, narrower scope). Generic phrases such as "overlapping contribution" or "not as important" count as non-specific.

If the section has fewer than 3 rows or more than half of the reasons are generic/short, **Output Format is reduced by 1 point**.

### Bundled Scripts (soft check)

`generate_bibtex.py` and related bundled scripts are expected to produce high-quality BibTeX: canonical `AuthorYYYY` keys and complete `title`, `author`, `year`, `journal`, and `doi` fields. The grader records whether the BibTeX meets this standard as a non-penalizing assertion; it does **not** directly affect the Output Format score.

## Interaction (0–10)

- **10**: Skill proactively asks about PDF download and (for Chinese prompts) Chinese literature; obeys explicit skip constraints.
- **8–9**: Asks most of the time; minor constraint handling issues.
- **5–7**: Misses one key question or ignores a soft constraint.
- **0–4**: Missing critical interaction or violates explicit constraint.

## Critical Caps

Caps are applied to the **total raw score** after summing the six dimensions.

| Violation | Cap | Notes |
|-----------|-----|-------|
| Fabricated DOI / journal / author | 40 | Use Crossref or DOI resolver to verify |
| Includes a forbidden decoy paper | 60 | From private-gold forbidden list |
| Wrong output language | 70 | e.g., Chinese summaries for English prompt |
| Missing or malformed BibTeX | 70 | Cannot be imported into reference manager |
| Does not ask about PDF download | 85 | Unless user explicitly pre-declined |
| Chinese prompt: no Chinese-literature question | 85 | Unless user explicitly pre-answered |

If multiple caps apply, use the **lowest** cap.
