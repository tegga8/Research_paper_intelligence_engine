#!/usr/bin/env python3
"""Terminal-first Research Paper Intelligence Engine.

This intentionally avoids the frontend/backend split. Run it with:

    python terminal_app.py

It uses ArXiv directly, stores papers in SQLite, and computes lightweight local
TF-IDF search/clustering so the project is useful from a plain terminal.
"""

from __future__ import annotations

import math
import sqlite3
import textwrap
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

DB_PATH = Path("research_terminal.db")
ARXIV_API = "https://export.arxiv.org/api/query"
ATOM = "{http://www.w3.org/2005/Atom}"


@dataclass
class Paper:
    id: int | None
    arxiv_id: str
    title: str
    abstract: str
    authors: str
    categories: str
    published_at: str
    pdf_url: str
    cluster: str = "Unclustered"

    @property
    def text(self) -> str:
        return f"{self.title}. {self.abstract}"


class TerminalResearchEngine:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                arxiv_id TEXT NOT NULL,
                title TEXT NOT NULL,
                abstract TEXT NOT NULL,
                authors TEXT NOT NULL,
                categories TEXT NOT NULL,
                published_at TEXT NOT NULL,
                pdf_url TEXT NOT NULL,
                cluster TEXT DEFAULT 'Unclustered',
                UNIQUE(topic, arxiv_id)
            )
            """
        )
        self.conn.commit()

    def fetch_arxiv(self, topic: str, max_papers: int) -> list[Paper]:
        query = urllib.parse.urlencode(
            {
                "search_query": f"all:{topic}",
                "start": 0,
                "max_results": max_papers,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            }
        )
        url = f"{ARXIV_API}?{query}"
        with urllib.request.urlopen(url, timeout=30) as response:
            xml_text = response.read()
        root = ET.fromstring(xml_text)
        papers: list[Paper] = []
        for entry in root.findall(f"{ATOM}entry"):
            arxiv_url = _text(entry, f"{ATOM}id")
            arxiv_id = arxiv_url.rsplit("/", 1)[-1]
            title = _clean(_text(entry, f"{ATOM}title"))
            abstract = _clean(_text(entry, f"{ATOM}summary"))
            published = _text(entry, f"{ATOM}published")[:10]
            authors = "; ".join(
                _text(author, f"{ATOM}name") for author in entry.findall(f"{ATOM}author")
            )
            categories = ",".join(
                category.attrib.get("term", "") for category in entry.findall(f"{ATOM}category")
            )
            pdf_url = arxiv_url.replace("/abs/", "/pdf/")
            for link in entry.findall(f"{ATOM}link"):
                if link.attrib.get("title") == "pdf" or link.attrib.get("type") == "application/pdf":
                    pdf_url = link.attrib.get("href", pdf_url)
                    break
            if arxiv_id and title:
                papers.append(
                    Paper(
                        id=None,
                        arxiv_id=arxiv_id,
                        title=title,
                        abstract=abstract,
                        authors=authors,
                        categories=categories,
                        published_at=published,
                        pdf_url=pdf_url,
                    )
                )
        return papers

    def save_papers(self, topic: str, papers: Iterable[Paper]) -> int:
        inserted = 0
        for paper in papers:
            cursor = self.conn.execute(
                """
                INSERT OR IGNORE INTO papers
                (topic, arxiv_id, title, abstract, authors, categories, published_at, pdf_url, cluster)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    topic,
                    paper.arxiv_id,
                    paper.title,
                    paper.abstract,
                    paper.authors,
                    paper.categories,
                    paper.published_at,
                    paper.pdf_url,
                    paper.cluster,
                ),
            )
            inserted += cursor.rowcount
        self.conn.commit()
        return inserted

    def papers_for_topic(self, topic: str) -> list[Paper]:
        rows = self.conn.execute(
            "SELECT * FROM papers WHERE topic = ? ORDER BY published_at DESC", (topic,)
        ).fetchall()
        return [_paper_from_row(row) for row in rows]

    def topics(self) -> list[tuple[str, int]]:
        rows = self.conn.execute(
            "SELECT topic, COUNT(*) as count FROM papers GROUP BY topic ORDER BY MAX(id) DESC"
        ).fetchall()
        return [(row["topic"], row["count"]) for row in rows]

    def semantic_search(self, topic: str, query: str, k: int = 8) -> list[tuple[Paper, float]]:
        papers = self.papers_for_topic(topic)
        if not papers:
            return []
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=5000)
            matrix = vectorizer.fit_transform([paper.text for paper in papers])
            query_vec = vectorizer.transform([query])
            scores = cosine_similarity(query_vec, matrix)[0]
            ranked = sorted(zip(papers, scores, strict=False), key=lambda item: item[1], reverse=True)
            return [(paper, float(score)) for paper, score in ranked[:k]]
        except Exception:
            return _keyword_search(papers, query, k)

    def cluster(self, topic: str, number_of_clusters: int = 5) -> dict[str, list[Paper]]:
        papers = self.papers_for_topic(topic)
        if not papers:
            return {}
        number_of_clusters = max(1, min(number_of_clusters, len(papers)))
        try:
            from sklearn.cluster import KMeans
            from sklearn.feature_extraction.text import TfidfVectorizer

            vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=3000)
            matrix = vectorizer.fit_transform([paper.text for paper in papers])
            model = KMeans(n_clusters=number_of_clusters, random_state=42, n_init="auto")
            labels = model.fit_predict(matrix)
            terms = vectorizer.get_feature_names_out()
            names: dict[int, str] = {}
            for label in sorted(set(labels)):
                center = model.cluster_centers_[label]
                top_terms = [terms[i] for i in center.argsort()[::-1][:3]]
                names[label] = " / ".join(term.title() for term in top_terms)
            grouped: dict[str, list[Paper]] = defaultdict(list)
            for paper, label in zip(papers, labels, strict=False):
                paper.cluster = names[int(label)]
                grouped[paper.cluster].append(paper)
                self.conn.execute("UPDATE papers SET cluster = ? WHERE id = ?", (paper.cluster, paper.id))
            self.conn.commit()
            return dict(grouped)
        except Exception:
            grouped = defaultdict(list)
            for paper in papers:
                name = (paper.categories.split(",")[0] or "General").strip()
                paper.cluster = name
                grouped[name].append(paper)
                self.conn.execute("UPDATE papers SET cluster = ? WHERE id = ?", (paper.cluster, paper.id))
            self.conn.commit()
            return dict(grouped)

    def dashboard(self, topic: str) -> dict[str, object]:
        papers = self.papers_for_topic(topic)
        months = Counter(paper.published_at[:7] for paper in papers if paper.published_at)
        clusters = Counter(paper.cluster for paper in papers)
        recent = papers[:5]
        return {
            "total": len(papers),
            "months": sorted(months.items()),
            "clusters": clusters.most_common(),
            "recent": recent,
        }

    def generate_literature_review(self, topic: str) -> str:
        papers = self.papers_for_topic(topic)
        clusters = defaultdict(list)
        for paper in papers:
            clusters[paper.cluster].append(paper)
        directions = "\n".join(
            f"- {cluster}: {len(items)} papers. Representative: {items[0].title}"
            for cluster, items in clusters.items()
        )
        references = "\n".join(
            f"- {paper.title} ({paper.published_at[:4]}). {paper.pdf_url}" for paper in papers[:12]
        )
        return f"""
Literature Review: {topic}
{'=' * (19 + len(topic))}

Introduction
------------
This terminal survey summarizes {len(papers)} ArXiv papers collected for "{topic}".

Major Research Directions
-------------------------
{directions or '- No clusters yet. Run clustering from the menu first.'}

Important Findings
------------------
The most recent papers indicate active work around the cluster themes above. Start with the
representative papers, then use semantic search to drill into methods, benchmarks, and limitations.

Research Gaps / Opportunities
-----------------------------
- Small clusters may indicate underexplored areas worth investigating.
- Recent clusters with few papers may be emerging topics.
- Compare abstracts across clusters to identify missing benchmarks or contradictory assumptions.

References
----------
{references}
""".strip()


def _paper_from_row(row: sqlite3.Row) -> Paper:
    return Paper(
        id=row["id"],
        arxiv_id=row["arxiv_id"],
        title=row["title"],
        abstract=row["abstract"],
        authors=row["authors"],
        categories=row["categories"],
        published_at=row["published_at"],
        pdf_url=row["pdf_url"],
        cluster=row["cluster"] or "Unclustered",
    )


def _text(element: ET.Element, path: str) -> str:
    found = element.find(path)
    return found.text.strip() if found is not None and found.text else ""


def _clean(value: str) -> str:
    return " ".join(value.split())


def _keyword_search(papers: list[Paper], query: str, k: int) -> list[tuple[Paper, float]]:
    query_terms = set(query.lower().split())
    scored = []
    for paper in papers:
        terms = set(paper.text.lower().split())
        overlap = len(query_terms & terms)
        score = overlap / math.sqrt(max(len(terms), 1))
        scored.append((paper, score))
    return sorted(scored, key=lambda item: item[1], reverse=True)[:k]


def sample_papers(topic: str) -> list[Paper]:
    today = datetime_today()
    examples = [
        (
            f"Retrieval and Evaluation Methods for {topic}",
            f"This sample paper studies retrieval, benchmarking, and evaluation protocols for {topic}. It is included so the terminal interface works even when ArXiv is unreachable.",
            "cs.IR,cs.CL",
        ),
        (
            f"Scalable Representation Learning in {topic}",
            f"This work explores embedding-based methods, similarity search, and clustering for organizing literature about {topic}.",
            "cs.LG",
        ),
        (
            f"Open Problems and Future Directions in {topic}",
            f"The paper identifies limitations, underexplored subtopics, and research opportunities for {topic}.",
            "cs.AI",
        ),
        (
            f"Benchmark Datasets for {topic}",
            f"This study compares datasets, metrics, and experimental protocols used to evaluate systems related to {topic}.",
            "cs.CL,cs.AI",
        ),
        (
            f"A Survey of Recent Advances in {topic}",
            f"A survey-style overview of methods, applications, and emerging trends across recent {topic} research.",
            "cs.DL",
        ),
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
            published_at=f"{today[:4]}-{index:02d}-01",
            pdf_url="https://arxiv.org/",
        )
        for index, (title, abstract, categories) in enumerate(examples, start=1)
    ]


def datetime_today() -> str:
    from datetime import date

    return date.today().isoformat()


def print_box(title: str) -> None:
    print("\n" + "=" * 88)
    print(title)
    print("=" * 88)


def print_paper(paper: Paper, score: float | None = None) -> None:
    prefix = f"Score {score:.3f} | " if score is not None else ""
    print(f"\n{prefix}{paper.title}")
    print(f"Authors: {paper.authors[:120]}")
    print(f"Published: {paper.published_at} | Categories: {paper.categories} | Cluster: {paper.cluster}")
    print(textwrap.fill(paper.abstract, width=100, initial_indent="Summary: ", subsequent_indent="         "))
    print(f"PDF: {paper.pdf_url}")


def choose_topic(engine: TerminalResearchEngine) -> str | None:
    topics = engine.topics()
    if not topics:
        return None
    print_box("Saved Topics")
    for index, (topic, count) in enumerate(topics, start=1):
        print(f"{index}. {topic} ({count} papers)")
    choice = input("Choose a topic number, or press Enter to use the newest: ").strip()
    if not choice:
        return topics[0][0]
    if choice.isdigit() and 1 <= int(choice) <= len(topics):
        return topics[int(choice) - 1][0]
    return None


def main() -> None:
    engine = TerminalResearchEngine()
    current_topic = choose_topic(engine)
    while True:
        print_box("Research Paper Intelligence Engine - Terminal Mode")
        print(f"Current topic: {current_topic or 'None'}")
        print("1. Download papers from ArXiv")
        print("2. Show dashboard")
        print("3. Semantic search")
        print("4. Cluster papers")
        print("5. Generate literature review")
        print("6. Switch saved topic")
        print("0. Exit")
        choice = input("Select an option: ").strip()

        if choice == "1":
            topic = input("Topic, e.g. Large Language Models: ").strip()
            if not topic:
                print("Please enter a topic.")
                continue
            max_papers_text = input("How many papers? [50]: ").strip() or "50"
            max_papers = max(1, min(int(max_papers_text), 300))
            print(f"Downloading up to {max_papers} papers for '{topic}'...")
            try:
                papers = engine.fetch_arxiv(topic, max_papers)
                source = "ArXiv"
            except Exception as exc:
                print(f"ArXiv download failed: {exc}")
                print("Loading a small built-in sample dataset so you can still use the app offline.")
                papers = sample_papers(topic)
                source = "built-in sample"
            inserted = engine.save_papers(topic, papers)
            current_topic = topic
            print(f"Saved {inserted} new papers ({len(papers)} returned by {source}).")

        elif choice == "2":
            if not current_topic:
                print("Download or choose a topic first.")
                continue
            dashboard = engine.dashboard(current_topic)
            print_box(f"Dashboard: {current_topic}")
            print(f"Total papers: {dashboard['total']}")
            print("\nPapers per month:")
            for month, count in dashboard["months"][-12:]:
                print(f"  {month}: {'█' * min(count, 40)} {count}")
            print("\nClusters:")
            for cluster, count in dashboard["clusters"]:
                print(f"  {cluster}: {count}")
            print("\nRecent papers:")
            for paper in dashboard["recent"]:
                print_paper(paper)

        elif choice == "3":
            if not current_topic:
                print("Download or choose a topic first.")
                continue
            query = input("Search query: ").strip()
            if not query:
                continue
            for paper, score in engine.semantic_search(current_topic, query):
                print_paper(paper, score)

        elif choice == "4":
            if not current_topic:
                print("Download or choose a topic first.")
                continue
            n_text = input("Number of clusters [5]: ").strip() or "5"
            grouped = engine.cluster(current_topic, int(n_text))
            print_box("Clusters")
            for cluster, papers in sorted(grouped.items(), key=lambda item: len(item[1]), reverse=True):
                print(f"\n{cluster} ({len(papers)} papers)")
                for paper in papers[:3]:
                    print(f"  - {paper.title}")

        elif choice == "5":
            if not current_topic:
                print("Download or choose a topic first.")
                continue
            print_box("Literature Review")
            print(engine.generate_literature_review(current_topic))

        elif choice == "6":
            selected = choose_topic(engine)
            if selected:
                current_topic = selected

        elif choice == "0":
            print("Goodbye.")
            break

        else:
            print("Unknown option.")


if __name__ == "__main__":
    main()
