# Research Paper Intelligence Engine

A **terminal-first** research paper intelligence tool for ArXiv. For now, there is no need to run a web frontend, backend server, Docker, or deployment stack. Start the project in your terminal, enter a research topic, download papers, search them, cluster them, and generate a lightweight literature review.

## Fastest way to run

Install Python 3.11+ and then run:

```bash
python terminal_app.py
```

Or on macOS/Linux:

```bash
make cli
```

The terminal menu lets you:

1. Download papers from ArXiv for a topic.
2. Show a dashboard with counts, monthly trends, recent papers, and clusters.
3. Search papers semantically using local TF-IDF similarity.
4. Cluster papers into research directions.
5. Generate a literature-review style summary.
6. Switch between saved topics.

If ArXiv is blocked or offline, the app automatically loads a small built-in sample dataset so the menu, dashboard, search, clustering, and review generation still work.

Data is saved locally in:

```text
research_terminal.db
```

You can delete that file any time to reset the terminal app.

## Optional better search and clustering

The terminal app runs with the Python standard library for downloading and storage. If `scikit-learn` is installed, it automatically uses TF-IDF search and KMeans clustering.

Install the lightweight backend requirements if you want the better local ranking/clustering behavior:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python terminal_app.py
```

On Windows PowerShell:

```powershell
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r backend/requirements.txt
python terminal_app.py
```

## What the terminal interface does

### Download papers

Choose option `1`, enter a topic like:

```text
Large Language Models
```

Then choose how many papers to download. The app calls the ArXiv API and stores paper metadata locally:

- title
- abstract
- authors
- categories
- publication date
- PDF URL

### Dashboard

Choose option `2` to see:

- total papers
- papers per month
- current clusters
- recent papers
- paper summaries and PDF links

### Semantic search

Choose option `3` and ask things like:

```text
Recent papers on RAG evaluation
```

The app returns matching papers with scores, summaries, dates, authors, categories, and PDF links.

### Clustering

Choose option `4` to group papers into research directions. If `scikit-learn` is available, clusters are named from top TF-IDF terms.

### Literature review

Choose option `5` to generate a terminal literature-review style report with:

- introduction
- major research directions
- important findings
- research gaps / opportunities
- references

## Current project structure

```text
terminal_app.py      Simple terminal interface; use this first
backend/             Optional FastAPI/service code kept for later expansion
frontend/            Optional web UI prototype kept for later expansion
scripts/             Optional local setup helpers for the web version
data/                Sample metadata
```

For now, ignore `backend/` and `frontend/` unless you decide later that you want the web version again.

## If you still want the web version later

The local web setup is still present, but it is no longer the recommended starting point.

macOS/Linux:

```bash
./scripts/setup-local.sh
./scripts/start-local.sh
```

Windows PowerShell:

```powershell
./scripts/setup-local.ps1
./scripts/start-local.ps1
```

Then open:

- Frontend: <http://localhost:3000>
- Backend API docs: <http://127.0.0.1:8000/docs>
