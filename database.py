"""SQLite persistence and ArXiv ingestion for the terminal research engine."""

from __future__ import annotations

import sqlite3
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
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


class PaperDatabase:
    """Small SQLite repository used by the local CLI application."""

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
        from topic_relevance import build_arxiv_query, rank_topic_relevance

        requested = max(1, max_papers)
        fetch_size = min(max(requested * 4, 50), 1000)
        papers = self._fetch_arxiv_query(build_arxiv_query(topic), fetch_size)
        if not papers:
            papers = self._fetch_arxiv_query(f"all:{topic}", fetch_size)
        return rank_topic_relevance(topic, papers, requested)

    def _fetch_arxiv_query(self, search_query: str, max_papers: int) -> list[Paper]:
        query = urllib.parse.urlencode(
            {
                "search_query": search_query,
                "start": 0,
                "max_results": max_papers,
                "sortBy": "relevance",
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

    def update_cluster(self, paper_id: int | None, cluster: str) -> None:
        if paper_id is not None:
            self.conn.execute("UPDATE papers SET cluster = ? WHERE id = ?", (cluster, paper_id))

    def commit(self) -> None:
        self.conn.commit()


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
