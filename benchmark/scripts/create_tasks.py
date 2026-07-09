#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate public benchmark tasks for econ-compass."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

TASKS = [
    {
        "id": "E001",
        "name": "Chinese labor economics broad field",
        "prompt": "帮我找 10 篇劳动经济学最重要的论文，我需要快速了解这个领域的研究脉络。",
        "expected_output_language": "zh",
        "domain_type": "predefined",
        "expected_n": 10,
        "constraints": {
            "pdf_download": "ask",
            "chinese_literature_question": True,
            "must_cover_branches": [
                "Labor supply",
                "Human capital",
                "Wage determination and inequality",
                "Unemployment and search/matching",
                "Discrimination",
                "Immigration",
                "Labor market institutions",
                "Intergenerational mobility"
            ]
        },
        "notes_for_graders": "Chinese summaries and justifications expected. Skill should proactively ask about Chinese literature and PDF download."
    },
    {
        "id": "E002",
        "name": "English development economics",
        "prompt": "Find me the 10 most important papers in development economics.",
        "expected_output_language": "en",
        "domain_type": "predefined",
        "expected_n": 10,
        "constraints": {
            "pdf_download": "ask",
            "chinese_literature_question": False,
            "must_cover_branches": [
                "Institutions and governance",
                "Human capital",
                "Credit markets and microfinance",
                "Agricultural and rural development",
                "Conflict and development",
                "RCT and experimental methods",
                "Poverty and inequality measurement"
            ]
        },
        "notes_for_graders": "English output. Should ask about PDF download. No Chinese literature question."
    },
    {
        "id": "E003",
        "name": "Asset pricing post-1990",
        "prompt": "Curate the foundational literature on asset pricing. Focus on post-1990 work. Give me 12 papers.",
        "expected_output_language": "en",
        "domain_type": "predefined",
        "expected_n": 12,
        "constraints": {
            "pdf_download": "ask",
            "chinese_literature_question": False,
            "must_cover_branches": [
                "Factor models",
                "Equity premium puzzle",
                "Consumption-based asset pricing",
                "Behavioral asset pricing",
                "Liquidity and asset pricing",
                "Market efficiency and anomalies"
            ]
        },
        "notes_for_graders": "All selected papers should be from 1990 or later due to explicit constraint."
    },
    {
        "id": "E004",
        "name": "Behavioral economics",
        "prompt": "What are the must-read papers in behavioral economics? I need 8 essential ones.",
        "expected_output_language": "en",
        "domain_type": "predefined",
        "expected_n": 8,
        "constraints": {
            "pdf_download": "ask",
            "chinese_literature_question": False,
            "must_cover_branches": [
                "Prospect theory and loss aversion",
                "Time inconsistency",
                "Social preferences",
                "Heuristics and biases",
                "Nudge and choice architecture",
                "Behavioral finance"
            ]
        },
        "notes_for_graders": "English output. Should cover both classic Tversky-Kahneman and modern applied behavioral papers."
    },
    {
        "id": "E005",
        "name": "Digitalization and firm innovation",
        "prompt": "I need to understand the literature on digitalization and firm innovation. Find me the 8 most essential papers.",
        "expected_output_language": "en",
        "domain_type": "thematic",
        "expected_n": 8,
        "constraints": {
            "pdf_download": "ask",
            "chinese_literature_question": False,
            "must_cover_branches": [
                "Digital technology and firm productivity",
                "Platform economics and market structure",
                "Data and firm strategy",
                "AI and automation",
                "Digital divide and inequality"
            ]
        },
        "notes_for_graders": "This is not a predefined subfield; skill should use thematic clustering."
    },
    {
        "id": "E006",
        "name": "Chinese carbon pricing English-only",
        "prompt": "给我找 5 篇关于碳定价的经济学经典论文，要英文的",
        "expected_output_language": "zh",
        "domain_type": "thematic",
        "expected_n": 5,
        "constraints": {
            "pdf_download": "ask",
            "chinese_literature_question": True,
            "must_cover_branches": [
                "Carbon tax theory",
                "Carbon trading / ETS",
                "Social cost of carbon",
                "Carbon pricing policy effects"
            ]
        },
        "notes_for_graders": "Chinese summaries but English paper metadata. Skill should ask about Chinese literature, then user replies 'English only'. Final list should still be English papers."
    },
    {
        "id": "E007",
        "name": "Financial econometrics cross-discipline",
        "prompt": "I need to understand financial econometrics. Give me 12 essential papers.",
        "expected_output_language": "en",
        "domain_type": "cross_discipline",
        "expected_n": 12,
        "constraints": {
            "pdf_download": "ask",
            "chinese_literature_question": False,
            "must_cover_branches": [
                "Time series (GARCH, stochastic volatility)",
                "Factor models and asset pricing tests",
                "High-frequency microstructure",
                "Forecasting and nowcasting",
                "Machine learning in finance",
                "Risk management and tail risk"
            ]
        },
        "notes_for_graders": "Cross-discipline between finance and econometrics; should weight methodological innovation and empirical significance."
    },
    {
        "id": "E008",
        "name": "Political economy of development",
        "prompt": "Find the 10 most important papers on political economy of development.",
        "expected_output_language": "en",
        "domain_type": "cross_discipline",
        "expected_n": 10,
        "constraints": {
            "pdf_download": "ask",
            "chinese_literature_question": False,
            "must_cover_branches": [
                "Colonial institutions and long-run development",
                "State capacity and bureaucracy",
                "Corruption and rent-seeking",
                "Conflict and political violence",
                "Democracy and elections",
                "Media and information"
            ]
        },
        "notes_for_graders": "Intersection of political economy and development."
    },
    {
        "id": "E009",
        "name": "Health economics small N",
        "prompt": "Recommend 5 must-read papers in health economics.",
        "expected_output_language": "en",
        "domain_type": "predefined",
        "expected_n": 5,
        "constraints": {
            "pdf_download": "ask",
            "chinese_literature_question": False,
            "must_cover_branches": [
                "Health production and demand",
                "Health insurance",
                "Provider behavior",
                "Pharmaceuticals and innovation"
            ]
        },
        "notes_for_graders": "Small N boundary test; skill should not produce 10 papers."
    },
    {
        "id": "E010",
        "name": "International trade large N",
        "prompt": "I am preparing for a field exam in international trade. Curate 20 canonical papers I absolutely must read.",
        "expected_output_language": "en",
        "domain_type": "predefined",
        "expected_n": 20,
        "constraints": {
            "pdf_download": "ask",
            "chinese_literature_question": False,
            "must_cover_branches": [
                "Comparative advantage",
                "Gravity models and trade costs",
                "Firm heterogeneity and trade",
                "Trade policy",
                "Trade and labor markets",
                "Global value chains",
                "Trade and development"
            ]
        },
        "notes_for_graders": "Large N boundary test."
    },
    {
        "id": "E011",
        "name": "Chinese labor economics no PDF",
        "prompt": "帮我找 8 篇劳动经济学必读论文，无需下载 PDF，只要清单。",
        "expected_output_language": "zh",
        "domain_type": "predefined",
        "expected_n": 8,
        "constraints": {
            "pdf_download": "skip_explicit",
            "chinese_literature_question": True,
            "must_cover_branches": [
                "Labor supply",
                "Human capital",
                "Wage determination and inequality",
                "Discrimination",
                "Immigration",
                "Labor market institutions"
            ]
        },
        "notes_for_graders": "User explicitly says no PDF download. Skill should skip Phase 7 and note this in output header."
    },
    {
        "id": "E012",
        "name": "Near-miss: introduce macroeconomics",
        "prompt": "Can you give me a brief introduction to macroeconomics?",
        "expected_output_language": "en",
        "domain_type": "boundary",
        "expected_n": None,
        "constraints": {
            "pdf_download": "default",
            "chinese_literature_question": False,
            "must_cover_branches": []
        },
        "notes_for_graders": "Near-miss trigger test. User asks for an introduction, not a curated reading list. Skill should not produce a reading list; it should answer the conceptual question or decline politely. A reading list would be over-triggering."
    },
    {
        "id": "E013",
        "name": "Near-miss: Python literature review",
        "prompt": "Help me write a Python script that summarizes a literature review from PDFs.",
        "expected_output_language": "en",
        "domain_type": "boundary",
        "expected_n": None,
        "constraints": {
            "pdf_download": "default",
            "chinese_literature_question": False,
            "must_cover_branches": []
        },
        "notes_for_graders": "Near-miss trigger test. This is a coding request, not a request to curate economics papers. Skill should not trigger."
    },
    {
        "id": "E014",
        "name": "Near-miss: textbooks recommendation",
        "prompt": "推荐几本经济学入门教材给我，不是论文。",
        "expected_output_language": "zh",
        "domain_type": "boundary",
        "expected_n": None,
        "constraints": {
            "pdf_download": "default",
            "chinese_literature_question": False,
            "must_cover_branches": []
        },
        "notes_for_graders": "Near-miss trigger test. User explicitly asks for textbooks, not papers. Skill should not produce a paper reading list."
    },
    {
        "id": "E015",
        "name": "Urban economics with decoy",
        "prompt": "Find 10 must-read papers in urban economics. I heard Glaeser's 'Triumph of the City' is very influential, so please include it if possible.",
        "expected_output_language": "en",
        "domain_type": "predefined",
        "expected_n": 10,
        "constraints": {
            "pdf_download": "ask",
            "chinese_literature_question": False,
            "must_cover_branches": [
                "Urban spatial structure",
                "Agglomeration economies",
                "Housing markets",
                "Transportation and commuting",
                "Neighborhood effects and segregation",
                "Place-based policies"
            ],
            "special_rules": [
                "Must NOT include Glaeser's 'Triumph of the City' because it is a book, not a research paper."
            ]
        },
        "notes_for_graders": "Anti-cheat decoy test. The skill should recognize that Triumph of the City is a popular book, not a canonical research paper, and exclude it."
    },
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed public benchmark task JSON files.")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing task files. Use with care; bundled JSON files are the source of truth.")
    args = parser.parse_args()

    tasks_dir = Path(__file__).resolve().parent.parent / "public" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)

    for task in TASKS:
        path = tasks_dir / f"{task['id']}.json"
        if path.exists() and not args.force:
            print(f"Skipped existing {path}; pass --force to overwrite")
            continue
        path.write_text(json.dumps(task, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote {path}")

    print("Note: bundled JSON task files are the benchmark source of truth; this legacy seeder intentionally does not overwrite by default.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
