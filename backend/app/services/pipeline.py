from sqlalchemy.orm import Session
from app.repositories import ClusterRepository, PaperRepository, ProjectRepository
from app.services.arxiv import ArxivClient
from app.services.clustering import ClusteringService
from app.services.embeddings import EmbeddingService, VectorIndex


class IntelligencePipeline:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.papers = PaperRepository(db)
        self.clusters = ClusterRepository(db)
        self.arxiv = ArxivClient()
        self.embeddings = EmbeddingService()
        self.index = VectorIndex()
        self.clustering = ClusteringService()

    async def build_project(self, topic: str, max_papers: int):
        project = self.projects.create(topic)
        self.projects.set_status(project, "ingesting")
        papers_data = await self.arxiv.search(topic, max_papers)
        if not papers_data:
            self.projects.set_status(project, "empty")
            return project
        paper_rows = self.papers.add_many(project.id, papers_data)
        self.projects.set_status(project, "embedding")
        texts = [f"{paper.title}. {paper.abstract}" for paper in paper_rows]
        vectors = self.embeddings.encode(texts)
        self.index.build(project.id, [paper.id for paper in paper_rows], vectors)
        self.projects.set_status(project, "clustering")
        cluster_rows, assignments, _ = self.clustering.cluster([paper.id for paper in paper_rows], texts, vectors)
        self.clusters.replace(project.id, cluster_rows, assignments)
        self.projects.set_status(project, "ready")
        self.db.refresh(project)
        return project
