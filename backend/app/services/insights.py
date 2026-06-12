from collections import Counter, defaultdict
from datetime import datetime
from statistics import mean
from sklearn.metrics.pairwise import cosine_similarity
from app.db.models import Cluster, Paper


def month_key(dt: datetime) -> str:
    return dt.strftime("%Y-%m")


class InsightService:
    def trend(self, papers: list[Paper]) -> tuple[list[dict], float]:
        counts = Counter(month_key(p.published_at) for p in papers)
        series = [{"month": key, "papers": counts[key]} for key in sorted(counts)]
        if len(series) < 2 or series[0]["papers"] == 0:
            return series, 0.0
        growth = (series[-1]["papers"] - series[0]["papers"]) / max(series[0]["papers"], 1)
        return series, round(growth * 100, 2)

    def opportunities(self, clusters: list[Cluster], papers: list[Paper]) -> list[dict]:
        by_cluster: dict[int, list[Paper]] = defaultdict(list)
        for paper in papers:
            if paper.cluster_id:
                by_cluster[paper.cluster_id].append(paper)
        opportunities = []
        for cluster in clusters:
            cluster_papers = by_cluster.get(cluster.id, [])
            recent_ratio = self._recent_ratio(cluster_papers)
            scarcity = 1 / max(len(cluster_papers), 1)
            score = min(10.0, 5 + recent_ratio * 3 + scarcity * 4)
            opportunities.append({
                "opportunity": f"Underexplored {cluster.name}",
                "reason": f"{len(cluster_papers)} papers found; recent publication ratio is {recent_ratio:.2f}; keywords: {cluster.keywords}.",
                "score": round(score, 1),
                "evidence": {
                    "paper_count": len(cluster_papers),
                    "recent_ratio": recent_ratio,
                    "top_keywords": cluster.keywords.split(",")[:5],
                },
            })
        return sorted(opportunities, key=lambda item: item["score"], reverse=True)[:6]

    def emerging_topics(self, clusters: list[Cluster], papers: list[Paper]) -> list[str]:
        paper_dates = [paper.published_at for paper in papers]
        if not paper_dates:
            return []
        midpoint = sorted(paper_dates)[len(paper_dates) // 2]
        scores = []
        for cluster in clusters:
            cluster_papers = [paper for paper in papers if paper.cluster_id == cluster.id]
            if not cluster_papers:
                continue
            recent = sum(p.published_at >= midpoint for p in cluster_papers)
            scores.append((recent / len(cluster_papers), cluster.name))
        return [name for _, name in sorted(scores, reverse=True)[:5]]

    def graph(self, clusters: list[Cluster], papers: list[Paper]) -> dict:
        nodes = [{"id": str(p.id), "label": p.title[:70], "size": max(8, p.citation_count + 8), "cluster": p.cluster_id} for p in papers]
        edges = []
        by_cluster: dict[int, list[Paper]] = defaultdict(list)
        for paper in papers:
            if paper.cluster_id:
                by_cluster[paper.cluster_id].append(paper)
        for group in by_cluster.values():
            leaders = sorted(group, key=lambda p: p.citation_count, reverse=True)[:3]
            for paper in group[:20]:
                for leader in leaders:
                    if paper.id != leader.id:
                        edges.append({"id": f"{paper.id}-{leader.id}", "source": str(paper.id), "target": str(leader.id)})
        return {"nodes": nodes, "edges": edges, "communities": [c.name for c in clusters]}

    def literature_review(self, topic: str, papers: list[Paper], clusters: list[Cluster]) -> str:
        refs = "\n".join(f"- {p.title} ({p.published_at.year}). {p.pdf_url}" for p in papers[:20])
        directions = "\n".join(f"- **{c.name}**: {c.summary}" for c in clusters)
        return f"""# Literature Review: {topic}

## Introduction
This survey synthesizes {len(papers)} papers retrieved from ArXiv for the topic **{topic}**.

## Major Research Directions
{directions}

## Important Findings
The collection concentrates around recurring methodological themes, benchmark construction, model design, and evaluation practice. Highly central papers should be reviewed first because they anchor the local citation and similarity graph.

## Methodological Trends
Recent work increasingly combines representation learning, retrieval, scalable evaluation, and modular system design. Cluster keywords expose the dominant methods and datasets.

## Current Limitations
The local corpus may underrepresent papers outside ArXiv, non-English work, and citation links unavailable in ArXiv metadata.

## Future Research Opportunities
Prioritize high-scoring gap opportunities, especially clusters with high growth and low paper counts.

## References
{refs}
"""

    def assistant_answer(self, question: str, papers: list[Paper], scores: list[float]) -> dict:
        snippets = []
        citations = []
        for paper, score in zip(papers, scores, strict=False):
            snippets.append(f"{paper.title}: {paper.abstract[:280]}")
            citations.append({"paper_id": paper.id, "title": paper.title, "score": round(score, 3), "pdf_url": paper.pdf_url})
        answer = "Based on the retrieved papers, " + " ".join(snippets[:3])
        confidence = round(mean(scores), 2) if scores else 0.0
        return {"answer": answer, "confidence": confidence, "citations": citations}

    def _recent_ratio(self, papers: list[Paper]) -> float:
        if not papers:
            return 0.0
        years = [p.published_at.year for p in papers]
        cutoff = max(years) - 1
        return sum(year >= cutoff for year in years) / len(years)
