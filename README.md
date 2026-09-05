# Research Paper Intelligence Engine

A **terminal-first ML research intelligence platform** for discovering, organizing, and analyzing ArXiv papers locally. The main workflow remains a local CLI:

```bash
python terminal_app.py
```

The app intentionally does **not** require React, NextJS, FastAPI, Flask, Docker, authentication, or cloud deployment for the terminal workflow.

## What it does

Given a topic such as **Large Language Models**, **Retrieval-Augmented Generation**, or **Computer Vision**, the terminal app can:

- Download ArXiv paper metadata into local SQLite with topic-aware query construction and relevance filtering.
- Generate transformer sentence embeddings with `sentence-transformers` and `all-MiniLM-L6-v2`.
- Store embeddings locally under `data/embeddings/`.
- Build and query a local FAISS vector index, with a NumPy fallback when FAISS is unavailable.
- Run semantic search with query embedding → vector retrieval → ranked papers.
- Recommend similar papers with nearest-neighbor search.
- Cluster papers with HDBSCAN when available, with KMeans fallback.
- Generate meaningful cluster names from top cluster keywords.
- Discover research gaps using cluster size, publication recency, and growth rate.
- Show trend dashboards with terminal charts for fastest-growing, most-active, and declining topics.
- Generate Gemini-assisted cluster summaries when `GEMINI_API_KEY` or `GOOGLE_API_KEY` exists, with local summarization fallback.
- Produce cluster-aware literature reviews and export reports to `exports/` in Markdown or TXT.
- Render a polished Rich-powered terminal UI with panels, tables, status indicators, and loading spinners.

## Install

Python 3.11+ is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python terminal_app.py
```

Windows PowerShell:

```powershell
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt
python terminal_app.py
```

If optional ML packages are missing, the app falls back gracefully where possible so it never crashes during normal terminal use.

## Terminal menu

The CLI includes:

1. Download papers from ArXiv
2. Dashboard
3. Semantic vector search
4. Cluster papers
5. Recommend Similar Papers
6. Research Gap Discovery
7. Research Trend Dashboard
8. Generate literature review
9. Export reports
10. Switch saved topic

## Local files

```text
research_terminal.db        SQLite paper metadata database
data/embeddings/*.npz       Stored paper embeddings and ID mappings
data/embeddings/*.faiss     FAISS vector indexes when faiss-cpu is installed
exports/                    Literature review, gap, and trend report exports
```

Delete `research_terminal.db`, `data/embeddings/`, or `exports/` to reset local generated artifacts.

## Project structure

```text
terminal_app.py       Main CLI entry point
database.py           SQLite persistence and ArXiv ingestion
embeddings.py         Sentence embeddings, local storage, FAISS retrieval
clustering.py         HDBSCAN/KMeans clustering and cluster naming
recommendation.py     Similar-paper recommendation system
gap_discovery.py      Research opportunity scoring
trend_analysis.py     Monthly/yearly cluster trend analytics
literature_review.py  Summaries, reviews, and report export helpers
terminal_ui.py        Rich terminal rendering helpers
backend/              Older optional service prototype, not required for CLI
frontend/             Older optional UI prototype, not required for CLI
```

