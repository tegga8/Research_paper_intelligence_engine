"""Publication trend analytics for clustered paper collections."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from typing import Sequence

from database import Paper


def month_key(value: str) -> str:
    return value[:7] if value else "Unknown"


def year_key(value: str) -> str:
    return value[:4] if value else "Unknown"


def analyze_trends(papers: Sequence[Paper]) -> dict[str, object]:
    by_cluster: dict[str, list[Paper]] = defaultdict(list)
    for paper in papers:
        by_cluster[paper.cluster or "Unclustered"].append(paper)
    clusters = []
    for cluster, items in by_cluster.items():
        monthly = Counter(month_key(paper.published_at) for paper in items)
        yearly = Counter(year_key(paper.published_at) for paper in items)
        months = sorted(monthly)
        years = sorted(yearly)
        monthly_growth = _growth([monthly[month] for month in months])
        yearly_growth = _growth([yearly[year] for year in years])
        recent_count = sum(_is_recent(paper.published_at) for paper in items)
        clusters.append(
            {
                "cluster": cluster,
                "count": len(items),
                "monthly": [(month, monthly[month]) for month in months],
                "yearly": [(year, yearly[year]) for year in years],
                "monthly_growth": monthly_growth,
                "yearly_growth": yearly_growth,
                "recent_count": recent_count,
                "activity": len(items) + recent_count,
            }
        )
    fastest = sorted(clusters, key=lambda item: (item["monthly_growth"], item["recent_count"]), reverse=True)[:5]
    active = sorted(clusters, key=lambda item: item["activity"], reverse=True)[:5]
    declining = sorted(clusters, key=lambda item: item["monthly_growth"])[:5]
    return {"clusters": clusters, "fastest": fastest, "active": active, "declining": declining}


def terminal_bar(count: int, max_width: int = 36) -> str:
    return "█" * min(max_width, max(1, count)) if count else ""


def _growth(values: list[int]) -> float:
    if len(values) < 2:
        return 0.0
    first = max(values[0], 1)
    return round(((values[-1] - values[0]) / first) * 100, 2)


def _is_recent(value: str) -> bool:
    try:
        year = int(value[:4])
        return year >= date.today().year - 1
    except Exception:
        return False
