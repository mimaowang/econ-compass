# Paper Selection Methodology

> This reference defines the systematic methodology for identifying and selecting the most important papers in any economics field, subfield, or research topic. Apply these criteria rigorously to every candidate paper.

## Core Principle

The goal is NOT to find the "top N most cited" papers. Citation counts are correlated with importance but are not a substitute for it. A paper can be highly cited for being a convenient reference, a survey, or a controversial finding that was later overturned.

Instead, the goal is to identify papers that are **canonical** — papers that, if removed from the field's intellectual history, would leave a gap that no other paper could fill.

---

## Multi-Dimensional Selection Criteria

Apply ALL five dimensions to each candidate paper. A paper does not need to score highly on every dimension, but it must excel on at least two and be defensible on all.

### Criterion 1: Foundational Contribution (Weight: HIGHEST)

**What to assess:**
- Did this paper create or fundamentally reshape a research program?
- Did it introduce a concept, framework, or empirical finding that became a cornerstone of the field?
- Did it open a new question that generated a substantial follow-up literature?
- Does the field's intellectual history change materially if this paper did not exist?

**Evidence sources:**
- Handbook chapters that devote entire sections to this paper
- JEL/JEP review articles that treat it as a landmark
- PhD syllabi that include it as required reading
- Papers that cite this one as foundational (not merely as a citation)

**Red flags:**
- Paper is widely cited but mainly as a data source or methodological footnote
- Paper summarized an existing literature without adding a novel framework
- Paper was important when published but later superseded by better work

---

### Criterion 2: Methodological or Empirical Innovation (Weight: HIGH)

**What to assess:**
- Did this paper introduce a new identification strategy that became widely adopted?
- Did it develop a structural estimation method that opened new empirical possibilities?
- Did it provide the first credible causal evidence on a core question?
- Did it introduce a new measurement approach or data source?

**Evidence sources:**
- Methodological papers that cite it as the origin of a technique
- Textbooks and "how-to" guides that reference its approach
- Subsequent papers that explicitly adopt its identification strategy

**Examples of high-scoring papers:**
- Card & Krueger (1994, AER): Natural experiment methodology in labor economics
- Chetty, Looney, Kroft (2009, AER): Salience and taxation in behavioral public economics
- Dell (2010, EMA): Geographic RDD for historical persistence
- Fama & French (1993, JFE): Three-factor model in asset pricing
- Melitz (2003, EMA): Firm heterogeneity in international trade
- Arellano & Bond (1991, RES): Dynamic panel GMM estimator

---

### Criterion 3: Empirical Significance and Robustness (Weight: MEDIUM)

**What to assess:**
- Is the empirical finding large in magnitude and economically significant?
- Has the finding been replicated or confirmed by independent studies?
- Does the finding change how economists think about the question?

**Evidence sources:**
- Replication studies
- Meta-analyses
- Consensus statements in review articles

**Red flags:**
- Finding is contested or not replicated
- Finding is statistically significant but economically trivial
- Finding is specific to a narrow context without generalizability

---

### Criterion 4: Coverage of Field Branches or Thematic Clusters (Weight: ESSENTIAL for the Set)

**What to assess:**
- Does the selected set of N papers collectively cover all major branches (or thematic clusters) of the field?
- Are there important branches with no representation?
- Is the balance between theoretical, structural, and reduced-form approaches reasonable?

**For matched predefined subfields:** Use `field-taxonomy.md` to verify branch coverage.

**For non-matched domains (e.g., "digitalization and firm innovation"):** Identify 3-5 thematic clusters within the topic. Each cluster should have at least one paper. Examples of cluster identification:
- For "digitalization and firm innovation": digital technologies and firm productivity, platform economics and market structure, data and firm strategy, AI and labor substitution, digital divide and inequality

**Principle:** A reading list that covers 3 out of 6 core branches of a subfield is incomplete regardless of how excellent the 3 selected papers are. Prioritize branch/cluster coverage.

---

### Criterion 5: Irreplaceability (Weight: DECISIVE)

**What to assess:**
- If this paper were removed from the reading list, could another paper substitute for it without significant loss?
- Does this paper provide something unique that no other paper provides?
- Is there another paper that covers the same branch/contribution equally well or better?

**This is the final filter.** After selecting candidate papers, ask for each one: "What would be lost if I replaced this with paper X?" If the answer is "nothing essential," replace it.

---

## Cross-Discipline Academic Standard Adjustments

Different fields have different notions of what makes a paper "important." Adjust the criteria weights accordingly:

| Discipline | Adjustment | Rationale |
|---|---|---|
| **Finance (Asset Pricing, Corporate Finance)** | Increase Criterion 3 (Empirical Significance) | Major empirical discoveries (e.g., Fama-French factors, IPO underpricing) can themselves be foundational. A paper that documents a robust new anomaly or empirical regularity is a classic in finance even without methodological innovation. |
| **Econometrics** | Increase Criterion 2 (Methodological Innovation) | In econometrics, the method IS the contribution. A new estimator (GMM, Lasso, BLP) is a canonical paper regardless of whether it applies the method to a specific empirical question. |
| **Complex/Agent-Based Economics** | Increase Criterion 1 (Paradigm Creation) | Introducing a new modeling paradigm (e.g., agent-based macro, network-based contagion) outweighs a single empirical finding. The field rewards conceptual breakthroughs. |
| **All other fields** | Use the default five-dimension framework as-is | The standard framework is optimized for mainstream applied and theoretical economics. |

---

## Validation Sources (in order of authority)

When in doubt about a paper's canonical status, consult these sources:

1. **PhD Field Course Syllabi** (Highest Authority)
   - Syllabi from top-20 economics PhD programs
   - If a paper appears on 5+ independent syllabi, it is canonical
   - Priority programs: MIT, Harvard, Chicago, Stanford, Berkeley, LSE, Princeton, Yale, Columbia, Northwestern, UPenn, NYU, UCLA, Michigan, Minnesota, Wisconsin, Duke, Brown, Cornell, UCSD

2. **Handbook Chapters**
   - Handbook of [Field] Economics chapters (see field-taxonomy.md for relevant handbooks)
   - If a paper is discussed at length (>2 paragraphs) in a handbook chapter, it is likely canonical

3. **Journal of Economic Literature (JEL) and Journal of Economic Perspectives (JEP) Review Articles**
   - These are authoritative surveys written by leading scholars
   - Papers featured prominently in multiple JEL/JEP articles are canonical

4. **Citation Count and Network Centrality** (Supporting Only)
   - Google Scholar citation count is a rough signal of broad attention
   - Network centrality within the field's citation graph is more informative
   - NEVER use citation count as the sole or primary criterion

5. **Awards and Recognition**
   - Clark Medal (John Bates Clark), Nobel Memorial Prize in Economic Sciences
   - Frisch Medal (Econometric Society), AEJ Best Paper Awards
   - Keynote lectures at top conferences: NBER Summer Institute, Econometric Society World Congress, AEA Annual Meeting

---

## Systematic Search Strategy

When beginning curation for any field:

### Step 1: Map the Field
Use `field-taxonomy.md` for matched fields, or identify thematic clusters for non-matched domains. This ensures no major area is overlooked.

### Step 2: Identify Anchor Papers
For each branch or cluster, identify the 1-2 most widely recognized papers. These are typically:
- Papers discussed in the opening paragraphs of handbook chapters
- Papers that appear on the most syllabi
- Papers that scholars name when asked "what should every graduate student read?"

### Step 3: Fill Branch Gaps
Ensure every core branch (or thematic cluster) has at least one paper. If a branch lacks a clear anchor paper, search specifically for the most influential paper in that branch.

### Step 4: Apply the Irreplaceability Filter
For each candidate, ask: "Is there another paper that covers the same ground better?" If yes, replace. If no, keep.

### Step 5: Verify Against Syllabi
Cross-check the final list against at least 3 PhD field course syllabi. If the list omits papers that appear on all syllabi, reconsider.

### Step 6: Balance the List
Ensure reasonable balance across:
- Theoretical vs. empirical
- Structural vs. reduced-form
- Classic (pre-2005) vs. contemporary (post-2010)
- Different methodological approaches

---

## Writing "Why Irreplaceable" (2-5 Sentences)

For each paper in the final list, write 2-5 concise sentences explaining its unique contribution. Prioritize substance over strict brevity — a 4-sentence explanation that captures a paper's genuine contribution is better than a 2-sentence one that is generic. These sentences must be substantive — avoid generic praise. Address:

1. **What unique contribution did this paper make?** (a new idea, method, or empirical finding)
2. **Why can no other paper substitute for it?** (what gap would be left if removed?)

**Examples of good "Why Irreplaceable" statements:**

> "Card & Krueger (1994) demonstrated that natural experiments could credibly estimate causal effects in labor economics, overturning the prior consensus that minimum wages reduce employment. This paper catalyzed the credibility revolution in applied microeconomics — no earlier paper combined a clean quasi-experimental design with a policy question of this importance."

> "Melitz (2003) introduced firm heterogeneity into trade models, showing that trade liberalization reallocates market share toward more productive firms. This single insight created the 'new new trade theory' and made the firm — rather than the country or industry — the central unit of analysis in international economics."

> "Fama & French (1993) constructed the three-factor model that became the workhorse benchmark for asset pricing, replacing the CAPM. Every subsequent factor model, and the entire factor zoo literature, builds on this foundation — it is impossible to study asset pricing without referencing it."

**Examples of bad "Why Irreplaceable" statements:**

> "This is a very important and highly cited paper that has influenced many researchers." (Too generic — all papers on the list should be important. Explain WHY.)

> "This paper uses instrumental variables to estimate the effect of X on Y." (Describes the method but not the contribution.)

### 中文示例

✅ 好示例：
"Card（1990）利用 Mariel 船民事件作为自然实验，首次用可信的因果推断识别了移民对本地劳动力市场的影响。它推翻了'移民必然压低本地工资'的简单结论，开创了移民经济学中的自然实验传统。如果没有这篇论文，后续关于移民的所有因果识别研究都会失去方法论起点。"

❌ 差示例：
"这篇论文非常重要，被广泛引用，对移民经济学产生了深远影响。"

**Length guidance:** 中文摘要和入选理由合计建议 150-300 字；英文建议 80-200 词。过短通常意味着理由不够具体。

---

## Common Pitfalls

1. **Recency bias**: Overweighting recent papers at the expense of foundational classics. A 2024 paper may be excellent but cannot have the same foundational status as a 1994 paper that shaped the field.

2. **Citation myopia**: Using citation count as the sole filter. A methods paper everyone cites for a specific technique may not be "important" in the sense of changing how the field thinks.

3. **Journal exclusivity**: Assuming only T5 papers matter. Many canonical papers appear in field tops (e.g., Bayer, Ferreira, McMillan 2007 in JPE is a counterexample — it IS in a T5, but the point stands: some canonical papers appear in field tops like JUE or JDE).

4. **Methodological homogeneity**: Selecting only reduced-form papers or only structural papers. The best reading lists include diverse methodological approaches.

5. **Branch neglect**: Focusing on the branches the curator knows best and ignoring important but less familiar branches.

6. **Synecdoche**: Assuming a paper that covers one branch well can represent the entire field. One paper, however excellent, cannot substitute for branch coverage.

7. **Speed trap**: Over-deliberating between two nearly equivalent papers. If two papers are genuinely close in importance, choose one, document the alternative, and move on. Perfectionism defeats the skill's speed promise.
