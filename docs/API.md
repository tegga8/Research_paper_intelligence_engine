# API Documentation

Base URL: `http://localhost:8000`

Interactive OpenAPI documentation is available at `/docs` when the backend is running.

## Projects

### `POST /api/projects`
Creates a project, searches ArXiv, stores metadata, builds embeddings, indexes FAISS vectors, clusters papers, and marks the project ready.

Request:

```json
{"topic":"Large Language Models","max_papers":500}
```

Response: project id, topic, status, and creation time.

### `GET /api/projects`
Lists research intelligence projects.

### `GET /api/projects/{project_id}/dashboard`
Returns dashboard cards, trend series, emerging topics, research opportunities, citation leaders, and recent papers.

## Intelligence endpoints

### `GET /api/search?project_id=1&query=Recent papers on RAG evaluation&k=10`
Semantic search over indexed title/abstract embeddings. Returns paper metadata, summary, similarity score, nearest-neighbor context, and reasoning.

### `GET /api/projects/{project_id}/clusters`
Returns automatic research clusters with generated names, summaries, keywords, counts, and representative papers.

### `GET /api/projects/{project_id}/gaps`
Returns research opportunities ranked by score with evidence such as scarcity, growth, and top keywords.

### `GET /api/projects/{project_id}/graph`
Returns nodes and edges for the citation/similarity community graph.

### `GET /api/papers/{paper_id}/recommendations?k=5`
Returns embedding-nearest paper recommendations and explanation text.

### `GET /api/projects/{project_id}/topics`
Returns latent topics derived from cluster keywords and representative papers.

## Generative endpoints

### `POST /api/reviews`
Generates an academic-style literature review for all papers, one cluster, or selected papers.

Request:

```json
{"project_id":1,"scope":"all","cluster_id":null,"paper_ids":[]}
```

### `POST /api/assistant`
Runs collection-aware RAG and returns answer text, confidence, and paper citations.

Request:

```json
{"project_id":1,"question":"What evaluation methods are used for RAG?","k":6}
```

## Evaluation

### `GET /api/projects/{project_id}/evaluation`
Returns Precision@K, Recall@K, silhouette score, cluster count, and recommendation similarity distribution fields.
