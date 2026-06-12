from datetime import datetime
from urllib.parse import urlencode
import feedparser
import httpx
from app.core.config import get_settings


class ArxivClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def search(self, topic: str, max_results: int) -> list[dict]:
        params = urlencode({
            "search_query": f"all:{topic}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        })
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{self.settings.arxiv_base_url}?{params}")
            response.raise_for_status()
        feed = feedparser.parse(response.text)
        papers: list[dict] = []
        for entry in feed.entries:
            arxiv_id = entry.id.rsplit("/", 1)[-1]
            pdf_url = next((link.href for link in entry.links if getattr(link, "type", "") == "application/pdf"), entry.id)
            papers.append({
                "arxiv_id": arxiv_id,
                "title": " ".join(entry.title.split()),
                "abstract": " ".join(entry.summary.split()),
                "authors": "; ".join(author.name for author in entry.authors),
                "categories": ",".join(tag.term for tag in entry.tags),
                "published_at": datetime(*entry.published_parsed[:6]),
                "pdf_url": pdf_url,
                "citation_count": 0,
            })
        return papers
