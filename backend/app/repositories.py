from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models import Cluster, Paper, Project


def serialize_paper(paper: Paper) -> dict:
    return {
        "id": paper.id,
        "arxiv_id": paper.arxiv_id,
        "title": paper.title,
        "abstract": paper.abstract,
        "authors": [a.strip() for a in paper.authors.split(";") if a.strip()],
        "categories": [c.strip() for c in paper.categories.split(",") if c.strip()],
        "published_at": paper.published_at,
        "pdf_url": paper.pdf_url,
        "citation_count": paper.citation_count,
        "cluster_id": paper.cluster_id,
    }


class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, topic: str) -> Project:
        project = Project(topic=topic, status="created")
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get(self, project_id: int) -> Project | None:
        return self.db.get(Project, project_id)

    def list(self) -> list[Project]:
        return list(self.db.scalars(select(Project).order_by(Project.created_at.desc())))

    def set_status(self, project: Project, status: str) -> None:
        project.status = status
        project.updated_at = datetime.utcnow()
        self.db.commit()


class PaperRepository:
    def __init__(self, db: Session):
        self.db = db

    def add_many(self, project_id: int, papers: list[dict]) -> list[Paper]:
        rows: list[Paper] = []
        for item in papers:
            paper = Paper(project_id=project_id, **item)
            self.db.add(paper)
            rows.append(paper)
        self.db.commit()
        for row in rows:
            self.db.refresh(row)
        return rows

    def by_project(self, project_id: int) -> list[Paper]:
        return list(self.db.scalars(select(Paper).where(Paper.project_id == project_id)))

    def get(self, paper_id: int) -> Paper | None:
        return self.db.get(Paper, paper_id)


class ClusterRepository:
    def __init__(self, db: Session):
        self.db = db

    def replace(self, project_id: int, clusters: list[dict], assignments: dict[int, int]) -> list[Cluster]:
        existing = list(self.db.scalars(select(Cluster).where(Cluster.project_id == project_id)))
        for cluster in existing:
            self.db.delete(cluster)
        self.db.flush()
        created: dict[int, Cluster] = {}
        for item in clusters:
            cluster = Cluster(project_id=project_id, **item)
            self.db.add(cluster)
            self.db.flush()
            created[item["label"]] = cluster
        papers = list(self.db.scalars(select(Paper).where(Paper.project_id == project_id)))
        for paper in papers:
            label = assignments.get(paper.id)
            paper.cluster_id = created[label].id if label in created else None
        self.db.commit()
        return list(created.values())

    def by_project(self, project_id: int) -> list[Cluster]:
        return list(self.db.scalars(select(Cluster).where(Cluster.project_id == project_id)))
