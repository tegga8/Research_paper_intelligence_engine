"""Transformer embeddings and FAISS-backed vector search for paper metadata."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
from typing import Sequence

import numpy as np

from database import Paper

EMBEDDING_DIR = Path("data/embeddings")
MODEL_NAME = "all-MiniLM-L6-v2"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "default"


def generate_embeddings(texts: Sequence[str]) -> np.ndarray:
    """Generate normalized sentence embeddings with a deterministic local fallback."""
    if not texts:
        return np.empty((0, 384), dtype="float32")
    if os.getenv("RPIE_DISABLE_TRANSFORMERS") or importlib.util.find_spec("sentence_transformers") is None:
        return _hashing_embeddings(texts)
    from sentence_transformers import SentenceTransformer

    try:
        model = SentenceTransformer(MODEL_NAME)
        vectors = model.encode(
            list(texts),
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(vectors, dtype="float32")
    except Exception:
        return _hashing_embeddings(texts)


def save_embeddings(topic: str, paper_ids: Sequence[int], embeddings: np.ndarray) -> Path:
    EMBEDDING_DIR.mkdir(parents=True, exist_ok=True)
    path = _embedding_path(topic)
    np.savez_compressed(path, paper_ids=np.asarray(paper_ids, dtype="int64"), embeddings=embeddings)
    return path


def load_embeddings(topic: str) -> tuple[list[int], np.ndarray]:
    path = _embedding_path(topic)
    if not path.exists():
        return [], np.empty((0, 384), dtype="float32")
    data = np.load(path)
    return data["paper_ids"].astype(int).tolist(), np.asarray(data["embeddings"], dtype="float32")


def ensure_embeddings(topic: str, papers: Sequence[Paper]) -> tuple[list[int], np.ndarray]:
    """Load cached embeddings or rebuild them when paper IDs have changed."""
    current_ids = [int(paper.id) for paper in papers if paper.id is not None]
    stored_ids, stored_vectors = load_embeddings(topic)
    if current_ids and stored_ids == current_ids and len(stored_vectors) == len(current_ids):
        ensure_faiss_index(topic, stored_vectors)
        return stored_ids, stored_vectors
    vectors = generate_embeddings([paper.text for paper in papers if paper.id is not None])
    save_embeddings(topic, current_ids, vectors)
    ensure_faiss_index(topic, vectors)
    return current_ids, vectors


def save_faiss_index(topic: str, embeddings: np.ndarray) -> Path | None:
    if embeddings.size == 0:
        return None
    if importlib.util.find_spec("faiss") is None:
        return None
    import faiss

    try:
        index = faiss.IndexFlatIP(int(embeddings.shape[1]))
        index.add(np.asarray(embeddings, dtype="float32"))
        path = _faiss_path(topic)
        path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(path))
        _metadata_path(topic).write_text(json.dumps({"metric": "cosine", "model": MODEL_NAME}, indent=2))
        return path
    except Exception:
        return None


def load_faiss_index(topic: str):
    path = _faiss_path(topic)
    if not path.exists():
        return None
    if importlib.util.find_spec("faiss") is None:
        return None
    import faiss

    try:
        return faiss.read_index(str(path))
    except Exception:
        return None


def ensure_faiss_index(topic: str, embeddings: np.ndarray) -> None:
    if not _faiss_path(topic).exists():
        save_faiss_index(topic, embeddings)


def search_by_embedding(topic: str, papers: Sequence[Paper], query: str, k: int = 8) -> list[tuple[Paper, float]]:
    if not papers or not query.strip():
        return []
    paper_ids, vectors = ensure_embeddings(topic, papers)
    if vectors.size == 0:
        return []
    query_vector = generate_embeddings([query])
    id_to_paper = {paper.id: paper for paper in papers}
    k = min(k, len(paper_ids))

    index = load_faiss_index(topic)
    if index is not None:
        distances, indices = index.search(np.asarray(query_vector, dtype="float32"), k)
        results = []
        for score, row_index in zip(distances[0], indices[0], strict=False):
            if row_index < 0 or row_index >= len(paper_ids):
                continue
            paper = id_to_paper.get(paper_ids[int(row_index)])
            if paper:
                results.append((paper, float(score)))
        return results

    scores = np.dot(vectors, query_vector[0])
    ranked = np.argsort(scores)[::-1][:k]
    return [
        (id_to_paper[paper_ids[index]], float(scores[index]))
        for index in ranked
        if paper_ids[index] in id_to_paper
    ]


def find_similar_papers(topic: str, papers: Sequence[Paper], selected_paper: Paper, k: int = 5) -> list[tuple[Paper, float]]:
    if selected_paper.id is None:
        return []
    paper_ids, vectors = ensure_embeddings(topic, papers)
    if selected_paper.id not in paper_ids or vectors.size == 0:
        return []
    source_index = paper_ids.index(selected_paper.id)
    query_vector = vectors[source_index : source_index + 1]
    id_to_paper = {paper.id: paper for paper in papers}
    index = load_faiss_index(topic)
    search_k = min(k + 1, len(paper_ids))
    if index is not None:
        distances, indices = index.search(np.asarray(query_vector, dtype="float32"), search_k)
        raw = [(int(i), float(s)) for s, i in zip(distances[0], indices[0], strict=False) if i >= 0]
    else:
        scores = np.dot(vectors, query_vector[0])
        raw = [(int(i), float(scores[i])) for i in np.argsort(scores)[::-1][:search_k]]
    results = []
    for row_index, score in raw:
        paper_id = paper_ids[row_index]
        if paper_id == selected_paper.id:
            continue
        paper = id_to_paper.get(paper_id)
        if paper:
            results.append((paper, score))
    return results[:k]


def _embedding_path(topic: str) -> Path:
    return EMBEDDING_DIR / f"{slugify(topic)}.npz"


def _faiss_path(topic: str) -> Path:
    return EMBEDDING_DIR / f"{slugify(topic)}.faiss"


def _metadata_path(topic: str) -> Path:
    return EMBEDDING_DIR / f"{slugify(topic)}.json"


def _hashing_embeddings(texts: Sequence[str], dimensions: int = 384) -> np.ndarray:
    vectors = np.zeros((len(texts), dimensions), dtype="float32")
    for row, text in enumerate(texts):
        tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]+", text.lower())
        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "little") % dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vectors[row, bucket] += sign
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms
