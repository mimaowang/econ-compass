# Econ Compass Benchmark

A rigorous benchmark suite for evaluating whether the `econ-compass` skill improves economics literature curation quality relative to a no-skill baseline.

## Design Philosophy

- **Public tasks, private gold:** Prompts and constraints are public; canonical papers, acceptable alternatives, forbidden decoys, and canaries live in `private-gold/` and are not shipped in public releases.
- **With-skill vs without-skill:** Every task is scored in both configurations to isolate the value added by the skill.
- **Execution-as-judge:** Format, metadata, BibTeX, and file checks are programmatic where possible.
- **Critical caps:** Severe failures such as fabricated metadata, forbidden decoys, wrong language, or malformed BibTeX cap the final score.
- **Repeated runs:** Multiple iterations measure variance and flaky behavior.

## Directory Structure

```text
benchmark/
  README.md
  public/
    schemas/                 JSON schemas for task, grading, and aggregate output
    tasks/                   Public benchmark prompts and constraints
    tasks-paraphrase/        Optional paraphrase variants, enabled with --include-paraphrases
    rubrics/                 Grading rubric and critical cap descriptions
    fixtures/                Public smoke-test fixtures
  private-gold/              Sealed gold standards; gitignored in public releases
    gold.json
  scripts/
    run_benchmark.py         Main benchmark runner
    grade_output.py          Score a single output
    aggregate_results.py     Aggregate grading.json into benchmark.json and benchmark.md
    format_checker.py        Programmatic format checks
    leak_check.py            Detect leakage of private gold
    test_pdf_download.py     Mock/live PDF download benchmark
  workspace/
    iteration-001/           Results of a benchmark run
```

## Score Dimensions (100 points + Critical Caps)

| Dimension | Max | What it measures |
|-----------|-----|------------------|
| Coverage | 20 | Core branches / thematic clusters are represented |
| Canonical Quality | 25 | Selected papers are genuinely canonical vs gold standard |
| Justification Quality | 20 | "Why Irreplaceable" is specific and non-generic |
| Evidence & Metadata | 10 | Complete and accurate DOI, authors, year, journal |
| Output Format | 10 | Markdown/BibTeX conform to templates; language consistency |
| Interaction | 15 | Asks about PDF/Chinese literature; obeys constraints |

### Critical Caps

- **Fabricated evidence** (fake DOI, fake journal, fake author): max 40
- **Forbidden decoy included**: max 60
- **Wrong output language**: max 70
- **Missing, malformed, or count-mismatched BibTeX**: max 70
- **Does not ask about PDF download when appropriate**: max 85
- **Chinese prompt does not ask about Chinese literature**: max 85

## Anti-Cheat Mechanisms

1. **Sealed gold standard:** The expected papers are not present in public files or prompts.
2. **Optional paraphrase tasks:** Run `--include-paraphrases` to include public paraphrase variants and reduce template matching.
3. **Canary strings:** Private gold can contain unique tokens; leakage is flagged if they appear in outputs.
4. **Cross-run consistency:** High variance across repeated runs flags flaky behavior.
5. **Baseline comparison:** A score matters only if `with_skill` meaningfully outperforms `without_skill`.

## How to Run

```bash
# 1. Simulate outputs to validate the scoring pipeline.
python benchmark/scripts/run_benchmark.py --mode simulate --iterations 3

# Optional: include public paraphrase variants.
python benchmark/scripts/run_benchmark.py --mode simulate --iterations 3 --include-paraphrases

# 2. Grade a single output against private gold.
python benchmark/scripts/grade_output.py   --task benchmark/public/tasks/E001.json   --output benchmark/workspace/iteration-001/E001/with_skill/output.md   --gold benchmark/private-gold/gold.json   --config with_skill   --bib benchmark/workspace/iteration-001/E001/with_skill/output.bib

# 3. Aggregate one iteration directory into benchmark.json and benchmark.md.
python benchmark/scripts/aggregate_results.py --workspace benchmark/workspace/iteration-003

# 4. Check for private-gold leakage.
python benchmark/scripts/leak_check.py   --workspace benchmark/workspace/iteration-003   --gold benchmark/private-gold/gold.json
```

`live` mode requires an executor command:

```bash
python benchmark/scripts/run_benchmark.py --mode live --executor "python path/to/executor.py" --iterations 3
```

The executor receives `EC_BENCHMARK_TASK`, `EC_BENCHMARK_CONFIG`, `EC_BENCHMARK_SKILL_PATH`, and `EC_BENCHMARK_OUTPUT` environment variables.

## Quality Gate

A release-quality `econ-compass` should satisfy:

- **with_skill mean score >= 80**
- **without_skill mean score <= 65**
- **delta >= +15 points**
- **critical-cap violation rate < 10%**
- **flaky eval rate < 15%** (stddev > 15 points across repeated runs)

## Public Release Note

`benchmark/private-gold/gold.json` is intentionally excluded from public releases. Public contributors can still run format checks, PDF mock tests, schema validation, and simulate mode where private gold is available locally.
