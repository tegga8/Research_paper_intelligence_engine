"""Embedding-based topic clustering with HDBSCAN and KMeans fallback."""

from __future__ import annotations

from collections import defaultdict
import importlib.util
from typing import Sequence

import numpy as np

from database import Paper, PaperDatabase
from embeddings import ensure_embeddings

GENERIC_RESEARCH_STOPWORDS = {
    "paper", "papers", "study", "studies", "method", "methods", "approach",
    "approaches", "model", "models", "system", "systems", "task", "tasks",
    "result", "results", "show", "shows", "using", "based", "propose",
    "proposes", "proposed", "new", "novel", "data", "dataset", "datasets",
    "research", "work", "works", "analysis", "performance",
    "experiments", "experimental",
}


def cluster_papers(topic: str, papers: Sequence[Paper], db: PaperDatabase, requested_clusters: int = 5) -> dict[str, list[Paper]]:
    if not papers:
        return {}
    paper_ids, vectors = ensure_embeddings(topic, papers)
    if len(paper_ids) < 2 or vectors.size == 0:
        return {"General Research": list(papers)}
    labels = _hdbscan_labels(vectors)
    if labels is None or len(set(labels) - {-1}) < 2:
        labels = _kmeans_labels(vectors, max(1, min(requested_clusters, len(papers))))
    names = name_clusters(papers, labels, vectors)
    grouped: dict[str, list[Paper]] = defaultdict(list)
    for paper, label in zip(papers, labels, strict=False):
        cluster_name = names.get(int(label), "General Research")
        paper.cluster = cluster_name
        grouped[cluster_name].append(paper)
        db.update_cluster(paper.id, cluster_name)
    db.commit()
    return dict(grouped)


def name_clusters(papers: Sequence[Paper], labels: Sequence[int], vectors: np.ndarray | None = None) -> dict[int, str]:
    if importlib.util.find_spec("sklearn") is None:
        return _category_names(papers, labels)
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer

    try:
        stop_words = list(set(ENGLISH_STOP_WORDS) | GENERIC_RESEARCH_STOPWORDS)
        vectorizer = TfidfVectorizer(stop_words=stop_words, ngram_range=(1, 3), max_features=3000, min_df=1)
        matrix = vectorizer.fit_transform([paper.text for paper in papers])
        terms = vectorizer.get_feature_names_out()
        names: dict[int, str] = {}
        for label in sorted(set(int(value) for value in labels)):
            rows = [index for index, value in enumerate(labels) if int(value) == label]
            weights = np.asarray(matrix[rows].mean(axis=0)).ravel()
            top_terms = _dedupe_terms([terms[index] for index in weights.argsort()[::-1][:12]])
            names[label] = _pretty_name(top_terms) if label != -1 else f"Emerging / Miscellaneous: {_pretty_name(top_terms)}"
        return names
    except Exception:
        return _category_names(papers, labels)


def cluster_keywords(papers: Sequence[Paper], max_keywords: int = 6) -> list[str]:
    if importlib.util.find_spec("sklearn") is None:
        return _simple_keywords(papers, max_keywords)
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer

    try:
        stop_words = list(set(ENGLISH_STOP_WORDS) | GENERIC_RESEARCH_STOPWORDS)
        vectorizer = TfidfVectorizer(stop_words=stop_words, ngram_range=(1, 3), max_features=1000, min_df=1)
        matrix = vectorizer.fit_transform([paper.text for paper in papers])
        weights = np.asarray(matrix.mean(axis=0)).ravel()
        terms = vectorizer.get_feature_names_out()
        return _dedupe_terms([terms[index] for index in weights.argsort()[::-1][: max_keywords * 3]])[:max_keywords]
    except Exception:
        return _simple_keywords(papers, max_keywords)


def _hdbscan_labels(vectors: np.ndarray) -> list[int] | None:
    if importlib.util.find_spec("hdbscan") is None:
        return None
    import hdbscan

    try:
        min_cluster_size = max(2, min(8, len(vectors) // 6 or 2))
        clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, metric="euclidean")
        return [int(value) for value in clusterer.fit_predict(vectors)]
    except Exception:
        return None


def _kmeans_labels(vectors: np.ndarray, number_of_clusters: int) -> list[int]:
    if importlib.util.find_spec("sklearn") is None:
        return [0 for _ in vectors]
    from sklearn.cluster import KMeans

    try:
        model = KMeans(n_clusters=number_of_clusters, random_state=42, n_init="auto")
        return [int(value) for value in model.fit_predict(vectors)]
    except Exception:
        return [0 for _ in vectors]


def _dedupe_terms(terms: Sequence[str]) -> list[str]:
    selected: list[str] = []
    for term in terms:
        if any(term in existing or existing in term for existing in selected):
            continue
        selected.append(term)
    return selected


def _pretty_name(terms: Sequence[str]) -> str:
    if not terms:
        return "General Research"
    phrase_terms = [term for term in terms if len(term.split()) >= 2]
    candidate = phrase_terms[0] if phrase_terms else terms[0]
    return candidate.title()


def _category_names(papers: Sequence[Paper], labels: Sequence[int]) -> dict[int, str]:
    names = {}
    for label in sorted(set(int(value) for value in labels)):
        rows = [index for index, value in enumerate(labels) if int(value) == label]
        category = papers[rows[0]].categories.split(",")[0] if rows else "General"
        names[label] = category or "General Research"
    return names


def _simple_keywords(papers: Sequence[Paper], max_keywords: int) -> list[str]:
    words: dict[str, int] = defaultdict(int)
    for paper in papers:
        for word in paper.text.lower().split():
            clean = word.strip(".,:;()[]")
            if len(clean) > 4:
                words[clean] += 1
    return [word for word, _ in sorted(words.items(), key=lambda item: item[1], reverse=True)[:max_keywords]]
