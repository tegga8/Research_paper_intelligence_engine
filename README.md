# Research Paper Intelligence Engine

A local-first full-stack application for discovering, organizing, analyzing, summarizing, clustering, and exploring research papers from ArXiv. The product is designed as a modern AI research intelligence dashboard rather than a chatbot.

## What it does

Given a topic such as **Large Language Models**, **Computer Vision**, or **AI for Agriculture**, the system can:

- Search ArXiv and persist paper metadata locally.
- Build semantic embeddings with `BAAI/bge-small-en-v1.5` when installed, with a deterministic local fallback for lightweight development.
- Index paper vectors with FAISS when installed, with a NumPy fallback for a zero-heavy-dependency local run.
- Run semantic search over a paper collection.
- Cluster a field with UMAP + HDBSCAN when installed, with KMeans fallback for small or lightweight datasets.
- Analyze trends, emerging topics, and publication growth.
- Generate literature reviews and research-gap opportunities.
- Build citation/community graphs with NetworkX.
- Recommend similar papers with explainable nearest neighbors.
- Provide a collection-aware RAG assistant with source citations.
- Display evaluation metrics such as Precision@K, Recall@K, silhouette score, and similarity distributions.

## Architecture

```text
backend/   FastAPI, SQLAlchemy, ArXiv ingestion, embeddings, clustering, insights
frontend/  Next.js, TypeScript, TailwindCSS, Recharts, React Flow
data/      sample data; local SQLite/FAISS artifacts can be stored here
scripts/   lightweight local setup and start scripts for macOS/Linux/Windows
```

SQLite is used by default through SQLAlchemy. Migrating to PostgreSQL later requires replacing `DATABASE_URL` with a PostgreSQL URL and adding Alembic migrations around the existing ORM models.

## Prerequisites

Install these on your PC:

- Python 3.11 or newer
- Node.js 20 or newer
- npm, included with Node.js

Docker is intentionally not required for this local version.

## Quick start without Docker

### macOS / Linux

```bash
./scripts/setup-local.sh
./scripts/start-local.sh
```

### Windows PowerShell

```powershell
./scripts/setup-local.ps1
./scripts/start-local.ps1
```

Then open:

- Frontend: <http://localhost:3000>
- Backend API docs: <http://127.0.0.1:8000/docs>

## Makefile shortcuts

On macOS/Linux you can also use:

```bash
make setup
make dev
```

`make setup` creates `backend/.venv`, installs backend Python requirements, and runs `npm install` in `frontend/`. `make dev` starts both the FastAPI backend and Next.js frontend locally.

## Manual setup

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

For tests and linting helpers:

```bash
pip install -r requirements-dev.txt
```

For the heavier ML stack:

```bash
pip install -r requirements-ml.txt
```

The base app remains runnable without these heavier ML packages by using local fallbacks.

### Frontend

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 npm run dev
```

## Seed sample dataset

After backend setup:

```bash
make seed
```

Or manually:

```bash
cd backend
source .venv/bin/activate
python scripts/seed_sample.py
```

The seed script loads a small offline sample collection so the dashboard works before a long ArXiv ingestion job is run.

## API quickstart

Create an intelligence project:

```bash
curl -X POST http://127.0.0.1:8000/api/projects \
  -H 'Content-Type: application/json' \
  -d '{"topic":"Large Language Models","max_papers":100}'
```

Run semantic search:

```bash
curl 'http://127.0.0.1:8000/api/search?project_id=1&query=Recent%20papers%20on%20RAG%20evaluation&k=10'
```

Generate a literature review:

```bash
curl -X POST http://127.0.0.1:8000/api/reviews \
  -H 'Content-Type: application/json' \
  -d '{"project_id":1,"scope":"all"}'
```

Ask the collection assistant:

```bash
curl -X POST http://127.0.0.1:8000/api/assistant \
  -H 'Content-Type: application/json' \
  -d '{"project_id":1,"question":"What evaluation methods are used for RAG?"}'
```

## Environment variables

| Name | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./research.db` | SQLAlchemy database URL |
| `FAISS_INDEX_DIR` | `.faiss` | Local vector index storage |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated frontend origins |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Frontend API base URL |
| `OPENAI_API_KEY` | unset | Optional future LLM provider key |

## Production notes for later

- Deployment artifacts were deliberately removed from this local-first version to keep the project light on your PC.
- When you are ready for deployment, add Docker or a platform-specific deployment target back as a separate task.
- Long-running ingestion/analysis is synchronous for local simplicity. In production, move project builds to a job queue with progress events.
- Every recommendation, cluster, and gap includes explanation metadata for inspectability.
