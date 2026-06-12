"""Research-gap scoring built from cluster size, recency, and growth."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from statistics import mean
from typing import Sequence

from database import Paper


def discover_research_gaps(papers: Sequence[Paper]) -> list[dict[str, object]]:
    by_cluster: dict[str, list[Paper]] = defaultdict(list)
    for paper in papers:
        by_cluster[paper.cluster or "Unclustered"].append(paper)
    opportunities = []
    current_year = date.today().year
    for cluster, items in by_cluster.items():
        years = [_year(paper.published_at) for paper in items if _year(paper.published_at)]
        avg_recency = mean([current_year - year for year in years]) if years else 10.0
        recent_ratio = sum(year >= current_year - 1 for year in years) / max(len(years), 1)
        growth_rate = _yearly_growth(years)
        scarcity = 1 / max(len(items), 1)
        score = min(10.0, 2.5 + recent_ratio * 3.0 + max(growth_rate, 0) * 2.0 + scarcity * 8.0)
        opportunities.append(
            {
                "cluster": cluster,
                "cluster_size": len(items),
                "average_publication_recency": round(avg_recency, 2),
                "growth_rate": round(growth_rate * 100, 2),
                "gap_score": round(score, 1),
                "reason": _reason(len(items), recent_ratio, growth_rate),
            }
        )
    return sorted(opportunities, key=lambda item: item["gap_score"], reverse=True)


def _year(value: str) -> int | None:
    try:
        return int(value[:4])
    except Exception:
        return None


def _yearly_growth(years: list[int]) -> float:
    if len(years) < 2:
        return 0.0
    counts = Counter(years)
    ordered = sorted(counts)
    first = counts[ordered[0]]
    last = counts[ordered[-1]]
    return (last - first) / max(first, 1)


def _reason(size: int, recent_ratio: float, growth_rate: float) -> str:
    signals = []
    if size <= 8:
        signals.append("limited literature")
    if recent_ratio >= 0.45:
        signals.append("strong recent publication activity")
    if growth_rate > 0:
        signals.append("rapid publication growth")
    if not signals:
        signals.append("moderate activity with room for deeper synthesis")
    return "Potential opportunity due to " + ", ".join(signals) + "."
