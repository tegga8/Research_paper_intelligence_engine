from datetime import datetime
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    topic: str = Field(min_length=2, max_length=200)
    max_papers: int = Field(default=100, ge=1, le=500)


class ProjectOut(BaseModel):
    id: int
    topic: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class PaperOut(BaseModel):
    id: int
    arxiv_id: str
    title: str
    abstract: str
    authors: list[str]
    categories: list[str]
    published_at: datetime
    pdf_url: str
    citation_count: int
    cluster_id: int | None = None


class SearchResult(BaseModel):
    paper: PaperOut
    summary: str
    similarity_score: float
    nearest_neighbors: list[str]
    reasoning: str


class ClusterOut(BaseModel):
    id: int
    label: int
    name: str
    summary: str
    keywords: list[str]
    paper_count: int
    representative_papers: list[PaperOut]


class DashboardOut(BaseModel):
    project: ProjectOut
    total_papers: int
    number_of_clusters: int
    emerging_topics: list[str]
    citation_leaders: list[PaperOut]
    research_opportunities: list[dict]
    recent_papers: list[PaperOut]
    papers_per_month: list[dict]
    growth_rate: float


class ReviewRequest(BaseModel):
    project_id: int
    scope: str = "all"
    cluster_id: int | None = None
    paper_ids: list[int] = []


class AssistantRequest(BaseModel):
    project_id: int
    question: str
    k: int = 6


class AssistantResponse(BaseModel):
    answer: str
    confidence: float
    citations: list[dict]


class RecommendationResponse(BaseModel):
    source_paper: PaperOut
    recommendations: list[SearchResult]


class EvaluationOut(BaseModel):
    semantic_search: dict
    clustering: dict
    recommendations: dict
