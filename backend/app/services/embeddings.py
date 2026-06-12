from pathlib import Path
import pickle
import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.core.config import get_settings


class EmbeddingService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.vectorizer = HashingVectorizer(n_features=384, alternate_sign=False, norm="l2")
        self._model = None

    def _sentence_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.settings.embedding_model)
        return self._model

    def encode(self, texts: list[str]) -> np.ndarray:
        try:
            vectors = self._sentence_model().encode(texts, normalize_embeddings=True, show_progress_bar=False)
            return np.asarray(vectors, dtype="float32")
        except Exception:
            return self.vectorizer.transform(texts).astype("float32").toarray()


class VectorIndex:
    def __init__(self) -> None:
        self.settings = get_settings()
        Path(self.settings.faiss_index_dir).mkdir(parents=True, exist_ok=True)

    def _path(self, project_id: int) -> Path:
        return Path(self.settings.faiss_index_dir) / f"project_{project_id}.pkl"

    def build(self, project_id: int, paper_ids: list[int], vectors: np.ndarray) -> None:
        try:
            import faiss
            index = faiss.IndexFlatIP(vectors.shape[1])
            index.add(vectors)
            payload = {"backend": "faiss", "paper_ids": paper_ids, "index": faiss.serialize_index(index)}
        except Exception:
            payload = {"backend": "numpy", "paper_ids": paper_ids, "vectors": vectors}
        self._path(project_id).write_bytes(pickle.dumps(payload))

    def search(self, project_id: int, query_vector: np.ndarray, k: int) -> list[tuple[int, float]]:
        payload = pickle.loads(self._path(project_id).read_bytes())
        paper_ids = payload["paper_ids"]
        if payload["backend"] == "faiss":
            import faiss
            index = faiss.deserialize_index(payload["index"])
            scores, idxs = index.search(query_vector.astype("float32"), k)
            return [(paper_ids[i], float(scores[0][pos])) for pos, i in enumerate(idxs[0]) if i >= 0]
        scores = cosine_similarity(query_vector, payload["vectors"])[0]
        order = np.argsort(scores)[::-1][:k]
        return [(paper_ids[i], float(scores[i])) for i in order]

    def vectors(self, project_id: int) -> tuple[list[int], np.ndarray]:
        payload = pickle.loads(self._path(project_id).read_bytes())
        if payload["backend"] == "faiss":
            import faiss
            index = faiss.deserialize_index(payload["index"])
            vectors = np.vstack([index.reconstruct(i) for i in range(index.ntotal)])
            return payload["paper_ids"], vectors
        return payload["paper_ids"], payload["vectors"]
