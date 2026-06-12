"""Literature-review and report generation utilities."""

from __future__ import annotations

import importlib.util
import os
from collections import defaultdict
from pathlib import Path
from typing import Sequence

from clustering import cluster_keywords
from database import Paper
from gap_discovery import discover_research_gaps

EXPORT_DIR = Path("exports")


def generate_cluster_summary(cluster: str, papers: Sequence[Paper]) -> str:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key and importlib.util.find_spec("google.generativeai") is not None:
        import google.generativeai as genai

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            snippets = "\n".join(f"- {paper.title}: {paper.abstract[:500]}" for paper in papers[:8])
            prompt = f"""Summarize this research cluster for an ML literature-review dashboard.
Cluster: {cluster}
Papers:
{snippets}
Return concise sections: Cluster Summary, Research Directions, Current Challenges, Future Opportunities."""
            response = model.generate_content(prompt)
            if response.text:
                return response.text.strip()
        except Exception:
            pass
    keywords = ", ".join(cluster_keywords(papers, max_keywords=6))
    representative = papers[0].title if papers else "No representative paper"
    return (
        f"Cluster Summary: {cluster} centers on {keywords or 'recurring methods and applications'}.\n"
        f"Research Directions: Start from representative work such as '{representative}'.\n"
        "Current Challenges: Evaluation coverage, reproducibility, and cross-paper comparability need careful review.\n"
        "Future Opportunities: Identify benchmark gaps, efficient variants, and unexplored combinations of methods."
    )


def generate_literature_review(topic: str, papers: Sequence[Paper]) -> str:
    by_cluster: dict[str, list[Paper]] = defaultdict(list)
    for paper in papers:
        by_cluster[paper.cluster or "Unclustered"].append(paper)
    gaps = discover_research_gaps(papers)[:6]
    theme_lines = []
    key_paper_lines = []
    challenge_lines = []
    direction_lines = []
    for cluster, items in sorted(by_cluster.items(), key=lambda item: len(item[1]), reverse=True):
        keywords = ", ".join(cluster_keywords(items, max_keywords=5))
        summary = generate_cluster_summary(cluster, items)
        theme_lines.append(f"### {cluster}\n- Papers: {len(items)}\n- Keywords: {keywords}\n- Summary: {summary}")
        for paper in items[:3]:
            key_paper_lines.append(f"- **{paper.title}** ({paper.published_at[:4]}): {paper.abstract[:220]}...")
        challenge_lines.append(f"- **{cluster}:** compare assumptions, benchmarks, and unresolved limitations across {len(items)} papers.")
        direction_lines.append(f"- **{cluster}:** pursue robust evaluation, efficient methods, and datasets that connect this cluster to adjacent themes.")
    gap_lines = [f"- **{gap['cluster']}** — Gap Score {gap['gap_score']}: {gap['reason']}" for gap in gaps]
    refs = [f"- {paper.title} ({paper.published_at[:4]}). {paper.pdf_url}" for paper in papers[:25]]
    return f"""# Literature Review: {topic}

## Introduction
This review synthesizes {len(papers)} locally indexed ArXiv papers about **{topic}** using transformer-style embeddings, vector retrieval, cluster analysis, and publication trends.

## Major Research Themes
{chr(10).join(theme_lines) or '- Run clustering first to identify research themes.'}

## Key Papers
{chr(10).join(key_paper_lines) or '- No papers available.'}

## Current Challenges
{chr(10).join(challenge_lines) or '- Add papers to identify challenges.'}

## Research Opportunities
{chr(10).join(gap_lines) or '- Run clustering and gap discovery to identify opportunities.'}

## Future Directions
{chr(10).join(direction_lines) or '- Add more papers to generate future directions.'}

## References
{chr(10).join(refs)}
""".strip()


def export_report(name: str, content: str, fmt: str = "md") -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    extension = "md" if fmt.lower().startswith("m") else "txt"
    safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name).strip("_")
    path = EXPORT_DIR / f"{safe_name}.{extension}"
    path.write_text(content, encoding="utf-8")
    return path
