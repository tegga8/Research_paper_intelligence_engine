from collections import Counter, defaultdict
import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score


class ClusteringService:
    def cluster(self, paper_ids: list[int], texts: list[str], vectors: np.ndarray) -> tuple[list[dict], dict[int, int], float]:
        labels, coords = self._labels_and_coords(vectors)
        keywords_by_label = self._keywords(texts, labels)
        assignments = {paper_id: int(label) for paper_id, label in zip(paper_ids, labels, strict=False)}
        clusters = []
        for label in sorted(set(labels)):
            indices = [i for i, item in enumerate(labels) if item == label]
            keywords = keywords_by_label[int(label)]
            name = " ".join(word.title() for word in keywords[:3]) or f"Cluster {label}"
            summary = f"Research direction focused on {', '.join(keywords[:6])}. Includes {len(indices)} papers with closely related abstracts."
            centroid = coords[indices].mean(axis=0) if len(indices) else np.zeros(2)
            clusters.append({
                "label": int(label),
                "name": name,
                "summary": summary,
                "keywords": ",".join(keywords),
                "x": float(centroid[0]),
                "y": float(centroid[1]),
            })
        score = 0.0
        if len(set(labels)) > 1 and len(labels) > len(set(labels)):
            score = float(silhouette_score(vectors, labels))
        return clusters, assignments, score

    def _labels_and_coords(self, vectors: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        n = len(vectors)
        try:
            import hdbscan
            import umap
            n_neighbors = min(15, max(2, n - 1))
            coords = umap.UMAP(n_components=2, n_neighbors=n_neighbors, random_state=42).fit_transform(vectors)
            labels = hdbscan.HDBSCAN(min_cluster_size=max(3, min(10, n // 8))).fit_predict(coords)
            if len(set(labels)) > 1 and not all(label == -1 for label in labels):
                labels = np.array([max(int(label), 0) for label in labels])
                return labels, coords
        except Exception:
            pass
        k = min(max(2, int(np.sqrt(max(n, 2)))), min(8, n))
        labels = KMeans(n_clusters=k, random_state=42, n_init="auto").fit_predict(vectors) if n >= 2 else np.zeros(n, dtype=int)
        coords = vectors[:, :2] if vectors.shape[1] >= 2 else np.column_stack([vectors[:, 0], np.zeros(n)])
        return labels, coords

    def _keywords(self, texts: list[str], labels: np.ndarray) -> dict[int, list[str]]:
        tfidf = TfidfVectorizer(stop_words="english", max_features=200, ngram_range=(1, 2))
        matrix = tfidf.fit_transform(texts)
        terms = np.array(tfidf.get_feature_names_out())
        result: dict[int, list[str]] = defaultdict(list)
        for label in sorted(set(labels)):
            rows = [i for i, value in enumerate(labels) if value == label]
            weights = np.asarray(matrix[rows].mean(axis=0)).ravel()
            result[int(label)] = terms[np.argsort(weights)[::-1][:10]].tolist()
        return result
