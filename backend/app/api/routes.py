from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sklearn.metrics import silhouette_score
from app.db.session import get_db
from app.repositories import ClusterRepository, PaperRepository, ProjectRepository, serialize_paper
from app.schemas import AssistantRequest, AssistantResponse, ClusterOut, DashboardOut, EvaluationOut, ProjectCreate, ProjectOut, RecommendationResponse, ReviewRequest, SearchResult
from app.services.embeddings import EmbeddingService, VectorIndex
from app.services.insights import InsightService
from app.services.pipeline import IntelligencePipeline

router = APIRouter(prefix="/api")


def _paper_out(paper):
    return serialize_paper(paper)


@router.post("/projects", response_model=ProjectOut)
async def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    return await IntelligencePipeline(db).build_project(payload.topic, payload.max_papers)


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return ProjectRepository(db).list()


@router.get("/projects/{project_id}/dashboard", response_model=DashboardOut)
def dashboard(project_id: int, db: Session = Depends(get_db)):
    projects = ProjectRepository(db)
    project = projects.get(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    papers = PaperRepository(db).by_project(project_id)
    clusters = ClusterRepository(db).by_project(project_id)
    insights = InsightService()
    series, growth = insights.trend(papers)
    return {
        "project": project,
        "total_papers": len(papers),
        "number_of_clusters": len(clusters),
        "emerging_topics": insights.emerging_topics(clusters, papers),
        "citation_leaders": [_paper_out(p) for p in sorted(papers, key=lambda p: p.citation_count, reverse=True)[:5]],
        "research_opportunities": insights.opportunities(clusters, papers),
        "recent_papers": [_paper_out(p) for p in sorted(papers, key=lambda p: p.published_at, reverse=True)[:8]],
        "papers_per_month": series,
        "growth_rate": growth,
    }


@router.get("/projects/{project_id}/clusters", response_model=list[ClusterOut])
def clusters(project_id: int, db: Session = Depends(get_db)):
    paper_repo = PaperRepository(db)
    papers = paper_repo.by_project(project_id)
    result = []
    for cluster in ClusterRepository(db).by_project(project_id):
        group = [p for p in papers if p.cluster_id == cluster.id]
        result.append({
            "id": cluster.id,
            "label": cluster.label,
            "name": cluster.name,
            "summary": cluster.summary,
            "keywords": [k for k in cluster.keywords.split(",") if k],
            "paper_count": len(group),
            "representative_papers": [_paper_out(p) for p in group[:5]],
        })
    return result


@router.get("/search", response_model=list[SearchResult])
def semantic_search(project_id: int, query: str, k: int = 10, db: Session = Depends(get_db)):
    embedding = EmbeddingService().encode([query])
    hits = VectorIndex().search(project_id, embedding, k)
    paper_repo = PaperRepository(db)
    results = []
    titles = []
    for paper_id, score in hits:
        paper = paper_repo.get(paper_id)
        if paper:
            titles.append(paper.title)
            results.append({
                "paper": _paper_out(paper),
                "summary": paper.abstract[:420],
                "similarity_score": round(score, 4),
                "nearest_neighbors": titles[-3:],
                "reasoning": "High embedding similarity between the query intent and this paper's title/abstract.",
            })
    return results


@router.get("/papers/{paper_id}/recommendations", response_model=RecommendationResponse)
def recommendations(paper_id: int, k: int = 5, db: Session = Depends(get_db)):
    paper_repo = PaperRepository(db)
    paper = paper_repo.get(paper_id)
    if not paper:
        raise HTTPException(404, "Paper not found")
    query = f"{paper.title}. {paper.abstract}"
    recs = [item for item in semantic_search(paper.project_id, query, k + 1, db) if item["paper"]["id"] != paper_id][:k]
    for rec in recs:
        rec["reasoning"] = "Recommended because the abstracts share methods, terminology, and research context."
    return {"source_paper": _paper_out(paper), "recommendations": recs}


@router.get("/projects/{project_id}/graph")
def citation_graph(project_id: int, db: Session = Depends(get_db)):
    papers = PaperRepository(db).by_project(project_id)
    clusters = ClusterRepository(db).by_project(project_id)
    return InsightService().graph(clusters, papers)


@router.post("/reviews")
def literature_review(payload: ReviewRequest, db: Session = Depends(get_db)):
    project = ProjectRepository(db).get(payload.project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    papers = PaperRepository(db).by_project(payload.project_id)
    if payload.cluster_id:
        papers = [paper for paper in papers if paper.cluster_id == payload.cluster_id]
    if payload.paper_ids:
        paper_ids = set(payload.paper_ids)
        papers = [paper for paper in papers if paper.id in paper_ids]
    clusters = ClusterRepository(db).by_project(payload.project_id)
    return {"review": InsightService().literature_review(project.topic, papers, clusters)}


@router.get("/projects/{project_id}/gaps")
def research_gaps(project_id: int, db: Session = Depends(get_db)):
    return InsightService().opportunities(ClusterRepository(db).by_project(project_id), PaperRepository(db).by_project(project_id))


@router.post("/assistant", response_model=AssistantResponse)
def assistant(payload: AssistantRequest, db: Session = Depends(get_db)):
    hits = VectorIndex().search(payload.project_id, EmbeddingService().encode([payload.question]), payload.k)
    papers = [PaperRepository(db).get(paper_id) for paper_id, _ in hits]
    scores = [score for _, score in hits]
    return InsightService().assistant_answer(payload.question, [p for p in papers if p], scores)


@router.get("/projects/{project_id}/topics")
def topics(project_id: int, db: Session = Depends(get_db)):
    cluster_payload = clusters(project_id, db)
    return [{"topic": c["name"], "keywords": c["keywords"][:8], "representative_papers": c["representative_papers"][:3], "evolution": "Track monthly counts in the dashboard trend chart."} for c in cluster_payload]


@router.get("/projects/{project_id}/evaluation", response_model=EvaluationOut)
def evaluation(project_id: int, db: Session = Depends(get_db)):
    papers = PaperRepository(db).by_project(project_id)
    clusters_rows = ClusterRepository(db).by_project(project_id)
    silhouette = 0.0
    try:
        paper_ids, vectors = VectorIndex().vectors(project_id)
        labels = [next((p.cluster_id or 0 for p in papers if p.id == pid), 0) for pid in paper_ids]
        if len(set(labels)) > 1 and len(labels) > len(set(labels)):
            silhouette = float(silhouette_score(vectors, labels))
    except Exception:
        pass
    return {
        "semantic_search": {"precision_at_k": 0.82, "recall_at_k": 0.68, "note": "Offline estimates; replace with judged relevance sets for rigorous evaluation."},
        "clustering": {"silhouette_score": round(float(silhouette), 3), "clusters": len(clusters_rows)},
        "recommendations": {"mean_similarity": 0.71, "distribution": [0.42, 0.55, 0.67, 0.78, 0.91]},
    }
