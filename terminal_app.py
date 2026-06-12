#!/usr/bin/env python3
"""Terminal-first Research Paper Intelligence Engine.

Run with:

    python terminal_app.py

The application stays local and CLI-only while using transformer embeddings,
FAISS retrieval, clustering, recommendations, trend analysis, research-gap
scoring, and exportable literature reviews.
"""

from __future__ import annotations

import urllib.parse
from collections import Counter
from datetime import date

import terminal_ui as ui
from clustering import cluster_papers
from database import DB_PATH, Paper, PaperDatabase
from embeddings import ensure_embeddings, search_by_embedding
from gap_discovery import discover_research_gaps
from literature_review import export_report, generate_literature_review
from recommendation import recommend_similar_papers
from trend_analysis import analyze_trends, terminal_bar


class TerminalResearchEngine:
    """Orchestrates persistence, ML features, and report generation for the CLI."""

    def __init__(self) -> None:
        self.db = PaperDatabase(DB_PATH)

    def fetch_arxiv(self, topic: str, max_papers: int) -> list[Paper]:
        return self.db.fetch_arxiv(topic, max_papers)

    def save_papers(self, topic: str, papers: list[Paper]) -> int:
        inserted = self.db.save_papers(topic, papers)
        self.refresh_vector_index(topic)
        return inserted

    def papers_for_topic(self, topic: str) -> list[Paper]:
        return self.db.papers_for_topic(topic)

    def topics(self) -> list[tuple[str, int]]:
        return self.db.topics()

    def refresh_vector_index(self, topic: str) -> None:
        papers = self.papers_for_topic(topic)
        ensure_embeddings(topic, papers)

    def semantic_search(self, topic: str, query: str, k: int = 8) -> list[tuple[Paper, float]]:
        return search_by_embedding(topic, self.papers_for_topic(topic), query, k=k)

    def cluster(self, topic: str, number_of_clusters: int = 5) -> dict[str, list[Paper]]:
        return cluster_papers(topic, self.papers_for_topic(topic), self.db, number_of_clusters)

    def dashboard(self, topic: str) -> dict[str, object]:
        papers = self.papers_for_topic(topic)
        trends = analyze_trends(papers)
        gaps = discover_research_gaps(papers)[:5]
        clusters = Counter(paper.cluster for paper in papers)
        recent = papers[:5]
        return {
            "total": len(papers),
            "cluster_count": len([cluster for cluster in clusters if cluster != "Unclustered"]),
            "clusters": clusters.most_common(),
            "recent": recent,
            "top_research_areas": clusters.most_common(5),
            "fastest_growing": trends["fastest"],
            "opportunities": gaps,
        }

    def recommendations(self, topic: str, paper_index: int) -> list[tuple[Paper, float]]:
        return recommend_similar_papers(topic, self.papers_for_topic(topic), paper_index, k=5)

    def gaps(self, topic: str) -> list[dict[str, object]]:
        return discover_research_gaps(self.papers_for_topic(topic))

    def trends(self, topic: str) -> dict[str, object]:
        return analyze_trends(self.papers_for_topic(topic))

    def literature_review(self, topic: str) -> str:
        return generate_literature_review(topic, self.papers_for_topic(topic))


def choose_topic(engine: TerminalResearchEngine) -> str | None:
    topics = engine.topics()
    if not topics:
        return None
    ui.table("Saved Topics", ["#", "Topic", "Papers"], [(idx, topic, count) for idx, (topic, count) in enumerate(topics, start=1)])
    choice = input("Choose a topic number, or press Enter to use the newest: ").strip()
    if not choice:
        return topics[0][0]
    if choice.isdigit() and 1 <= int(choice) <= len(topics):
        return topics[int(choice) - 1][0]
    ui.warning("Invalid topic selection.")
    return None


def require_topic(current_topic: str | None) -> bool:
    if current_topic:
        return True
    ui.warning("Download papers or choose a saved topic first.")
    return False


def sample_papers(topic: str) -> list[Paper]:
    today = date.today().isoformat()
    examples = [
        (f"Retrieval and Evaluation Methods for {topic}", f"This sample paper studies retrieval, benchmarking, and evaluation protocols for {topic}. It is included so the terminal interface works even when ArXiv is unreachable.", "cs.IR,cs.CL"),
        (f"Scalable Representation Learning in {topic}", f"This work explores embedding-based methods, similarity search, and clustering for organizing literature about {topic}.", "cs.LG"),
        (f"Open Problems and Future Directions in {topic}", f"The paper identifies limitations, underexplored subtopics, and research opportunities for {topic}.", "cs.AI"),
        (f"Benchmark Datasets for {topic}", f"This study compares datasets, metrics, and experimental protocols used to evaluate systems related to {topic}.", "cs.CL,cs.AI"),
        (f"A Survey of Recent Advances in {topic}", f"A survey-style overview of methods, applications, and emerging trends across recent {topic} research.", "cs.DL"),
        (f"Efficient Systems for {topic}", f"This paper studies efficient training, inference, indexing, and deployment constraints for {topic} systems.", "cs.LG,cs.DC"),
    ]
    safe_topic = urllib.parse.quote(topic.replace(" ", "_"))
    return [
        Paper(
            id=None,
            arxiv_id=f"sample-{index}-{safe_topic}",
            title=title,
            abstract=abstract,
            authors="Terminal Demo Dataset",
            categories=categories,
            published_at=f"{today[:4]}-{min(index, 12):02d}-01",
            pdf_url="https://arxiv.org/",
        )
        for index, (title, abstract, categories) in enumerate(examples, start=1)
    ]


def show_dashboard(engine: TerminalResearchEngine, topic: str) -> None:
    dashboard = engine.dashboard(topic)
    ui.header(topic, int(dashboard["total"]), int(dashboard["cluster_count"]))
    ui.table(
        "Research Dashboard",
        ["Metric", "Value"],
        [
            ("Total Papers", dashboard["total"]),
            ("Number of Clusters", dashboard["cluster_count"]),
            ("Recent Papers", len(dashboard["recent"])),
            ("Research Opportunities", len(dashboard["opportunities"])),
        ],
    )
    ui.table("Top Research Areas", ["Cluster", "Papers"], dashboard["top_research_areas"])
    ui.table(
        "Fastest Growing Areas",
        ["Cluster", "Monthly Growth", "Papers"],
        [(item["cluster"], f"{item['monthly_growth']}%", item["count"]) for item in dashboard["fastest_growing"]],
    )
    ui.table(
        "Research Opportunities",
        ["Opportunity", "Gap Score", "Reason"],
        [(item["cluster"], item["gap_score"], item["reason"]) for item in dashboard["opportunities"]],
    )
    for paper in dashboard["recent"]:
        ui.paper_panel(paper)


def show_recommendations(engine: TerminalResearchEngine, topic: str) -> None:
    papers = engine.papers_for_topic(topic)
    ui.table("Select Paper", ["#", "Title", "Date"], [(idx, paper.title, paper.published_at) for idx, paper in enumerate(papers[:25], start=1)])
    choice = input("Paper number: ").strip()
    if not choice.isdigit() or not 1 <= int(choice) <= min(len(papers), 25):
        ui.warning("Invalid paper selection.")
        return
    selected = papers[int(choice) - 1]
    ui.info(f"Finding nearest neighbors for: {selected.title}")
    for paper, score in engine.recommendations(topic, int(choice) - 1):
        ui.paper_panel(paper, score)


def show_gaps(engine: TerminalResearchEngine, topic: str) -> str:
    gaps = engine.gaps(topic)
    ui.table(
        "Potential Research Opportunities",
        ["Rank", "Topic", "Gap Score", "Cluster Size", "Avg Recency", "Growth", "Reason"],
        [
            (
                index,
                item["cluster"],
                item["gap_score"],
                item["cluster_size"],
                item["average_publication_recency"],
                f"{item['growth_rate']}%",
                item["reason"],
            )
            for index, item in enumerate(gaps, start=1)
        ],
    )
    lines = ["# Research Gap Report", ""]
    for index, item in enumerate(gaps, start=1):
        lines.append(f"{index}. {item['cluster']}\n   Gap Score: {item['gap_score']}\n   Reason: {item['reason']}\n")
    return "\n".join(lines)


def show_trends(engine: TerminalResearchEngine, topic: str) -> str:
    trends = engine.trends(topic)
    ui.table(
        "Fastest Growing Topics",
        ["Topic", "Monthly Growth", "Yearly Growth", "Papers"],
        [(item["cluster"], f"{item['monthly_growth']}%", f"{item['yearly_growth']}%", item["count"]) for item in trends["fastest"]],
    )
    ui.table("Most Active Topics", ["Topic", "Activity", "Papers"], [(item["cluster"], item["activity"], item["count"]) for item in trends["active"]])
    ui.table("Declining Topics", ["Topic", "Monthly Growth", "Papers"], [(item["cluster"], f"{item['monthly_growth']}%", item["count"]) for item in trends["declining"]])
    report = ["# Research Trend Report", ""]
    for item in trends["clusters"]:
        ui.table(
            f"Monthly Trend: {item['cluster']}",
            ["Month", "Papers", "Chart"],
            [(month, count, terminal_bar(count)) for month, count in item["monthly"][-12:]],
        )
        report.append(f"## {item['cluster']}\nMonthly growth: {item['monthly_growth']}%\nYearly growth: {item['yearly_growth']}%\n")
    return "\n".join(report)


def export_menu(engine: TerminalResearchEngine, topic: str) -> None:
    ui.table("Exports", ["#", "Report"], [(1, "Literature Review"), (2, "Research Gap Report"), (3, "Trend Report")])
    choice = input("Report to export: ").strip()
    fmt = input("Format [md/txt]: ").strip().lower() or "md"
    if choice == "1":
        content = engine.literature_review(topic)
        name = f"{topic}_literature_review"
    elif choice == "2":
        content = "# Research Gap Report\n" + "\n".join(
            f"- {item['cluster']}: Gap Score {item['gap_score']} — {item['reason']}"
            for item in engine.gaps(topic)
        )
        name = f"{topic}_gap_report"
    elif choice == "3":
        trends = engine.trends(topic)
        content = "# Research Trend Report\n" + "\n".join(
            f"- {item['cluster']}: monthly growth {item['monthly_growth']}%, yearly growth {item['yearly_growth']}%"
            for item in trends["clusters"]
        )
        name = f"{topic}_trend_report"
    else:
        ui.warning("Invalid export selection.")
        return
    path = export_report(name, content, fmt)
    ui.success(f"Exported report to {path}")


def main() -> None:
    engine = TerminalResearchEngine()
    current_topic = choose_topic(engine)
    while True:
        total = len(engine.papers_for_topic(current_topic)) if current_topic else 0
        clusters = len({paper.cluster for paper in engine.papers_for_topic(current_topic) if paper.cluster != "Unclustered"}) if current_topic else 0
        ui.header(current_topic, total, clusters)
        ui.menu()
        choice = input("Select an option: ").strip()

        if choice == "1":
            topic = input("Topic, e.g. Large Language Models: ").strip()
            if not topic:
                ui.warning("Please enter a topic.")
                continue
            max_papers_text = input("How many papers? [50]: ").strip() or "50"
            try:
                max_papers = max(1, min(int(max_papers_text), 300))
            except ValueError:
                max_papers = 50
            try:
                with ui.spinner(f"Downloading up to {max_papers} papers for '{topic}'..."):
                    papers = engine.fetch_arxiv(topic, max_papers)
                source = "ArXiv"
            except Exception as exc:
                ui.warning(f"ArXiv download failed: {exc}")
                ui.info("Loading a built-in sample dataset so the app still works offline.")
                papers = sample_papers(topic)
                source = "built-in sample"
            with ui.spinner("Generating embeddings and updating local FAISS index..."):
                inserted = engine.save_papers(topic, papers)
            current_topic = topic
            ui.success(f"Saved {inserted} new papers ({len(papers)} returned by {source}).")

        elif choice == "2" and require_topic(current_topic):
            show_dashboard(engine, current_topic)

        elif choice == "3" and require_topic(current_topic):
            query = input("Search query: ").strip()
            if query:
                with ui.spinner("Embedding query and searching FAISS index..."):
                    results = engine.semantic_search(current_topic, query)
                for paper, score in results:
                    ui.paper_panel(paper, score)

        elif choice == "4" and require_topic(current_topic):
            n_text = input("Number of fallback KMeans clusters [5]: ").strip() or "5"
            with ui.spinner("Clustering embeddings with HDBSCAN/KMeans fallback..."):
                grouped = engine.cluster(current_topic, int(n_text))
            ui.table("Clusters", ["Cluster", "Papers", "Representative Paper"], [(cluster, len(items), items[0].title) for cluster, items in sorted(grouped.items(), key=lambda item: len(item[1]), reverse=True)])

        elif choice == "5" and require_topic(current_topic):
            show_recommendations(engine, current_topic)

        elif choice == "6" and require_topic(current_topic):
            show_gaps(engine, current_topic)

        elif choice == "7" and require_topic(current_topic):
            show_trends(engine, current_topic)

        elif choice == "8" and require_topic(current_topic):
            with ui.spinner("Generating cluster-aware literature review..."):
                review = engine.literature_review(current_topic)
            ui.markdown(review)

        elif choice == "9" and require_topic(current_topic):
            export_menu(engine, current_topic)

        elif choice == "10":
            selected = choose_topic(engine)
            if selected:
                current_topic = selected

        elif choice == "0":
            ui.success("Goodbye.")
            break

        else:
            ui.warning("Unknown option.")


if __name__ == "__main__":
    main()
