# Research Paper Intelligence Engine

A production-oriented full-stack platform for discovering, organizing, analyzing, summarizing, clustering, and exploring research papers from ArXiv. The product is designed as an AI research intelligence dashboard, not a chatbot.

## What it does

Given a topic such as **Large Language Models**, **Computer Vision**, or **AI for Agriculture**, the system can:

- Search ArXiv and persist paper metadata locally.
- Build semantic embeddings with `BAAI/bge-small-en-v1.5` and index them with FAISS.
- Run semantic search over a paper collection.
- Cluster a field with UMAP + HDBSCAN, with KMeans fallback for small datasets.
- Analyze trends, emerging topics, and publication growth.
- Generate literature reviews and research-gap opportunities.
- Build citation/community graphs with NetworkX.
- Recommend similar papers with explainable nearest neighbors.
- Provide a collection-aware RAG assistant with source citations.
- Display evaluation metrics such as Precision@K, Recall@K, silhouette score, and similarity distributions.

## Architecture

```text
backend/   FastAPI, SQLAlchemy, FAISS/ML services, ArXiv ingestion
frontend/  Next.js, TypeScript, TailwindCSS, Recharts, React Flow
data/      SQLite database, FAISS indexes, sample data
docker/    Runtime images for local deployment
```

SQLite is used by default through SQLAlchemy. Migrating to PostgreSQL requires replacing `DATABASE_URL` with a PostgreSQL URL and adding Alembic migrations around the existing ORM models.

## One-command local run

```bash
make dev
```

Then open:

- Frontend: <http://localhost:3000>
- Backend API docs: <http://localhost:8000/docs>

## Manual setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .[ml,dev]
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Seed sample dataset

```bash
make seed
```

The seed script loads a small offline sample collection so the dashboard works before a long ArXiv ingestion job is run.

## API quickstart

Create an intelligence project:

```bash
curl -X POST http://localhost:8000/api/projects   -H 'Content-Type: application/json'   -d '{"topic":"Large Language Models","max_papers":500}'
```

Run semantic search:

```bash
curl 'http://localhost:8000/api/search?project_id=1&query=Recent%20papers%20on%20RAG%20evaluation&k=10'
```

Generate a literature review:

```bash
curl -X POST http://localhost:8000/api/reviews   -H 'Content-Type: application/json'   -d '{"project_id":1,"scope":"all"}'
```

Ask the collection assistant:

```bash
curl -X POST http://localhost:8000/api/assistant   -H 'Content-Type: application/json'   -d '{"project_id":1,"question":"What evaluation methods are used for RAG?"}'
```

## Environment variables

| Name | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./research.db` | SQLAlchemy database URL |
| `FAISS_INDEX_DIR` | `.faiss` | Local vector index storage |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated frontend origins |
| `OPENAI_API_KEY` | unset | Optional; when present, LLM summaries can use provider integrations |

## Production notes

- Heavy ML dependencies are optional extras so the API can run in constrained environments. When unavailable, deterministic TF-IDF and hashing fallbacks keep the product functional for local demos and CI.
- Long-running ingestion/analysis is represented as synchronous endpoints for simplicity. In production, move project builds to Celery/RQ/Arq with Redis and progress events.
- The persistence layer is repository-based and keeps SQLite-specific assumptions isolated.
- Every recommendation, cluster, and gap includes explanation metadata for inspectability.
