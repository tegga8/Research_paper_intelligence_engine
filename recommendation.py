"""Nearest-neighbor paper recommendation helpers."""

from __future__ import annotations

from typing import Sequence

from database import Paper
from embeddings import find_similar_papers


def recommend_similar_papers(topic: str, papers: Sequence[Paper], paper_index: int, k: int = 5) -> list[tuple[Paper, float]]:
    if paper_index < 0 or paper_index >= len(papers):
        return []
    return find_similar_papers(topic, papers, papers[paper_index], k=k)
