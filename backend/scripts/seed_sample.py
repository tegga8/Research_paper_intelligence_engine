from datetime import datetime
from app.db.session import Base, SessionLocal, engine
from app.repositories import ClusterRepository, PaperRepository, ProjectRepository
from app.services.clustering import ClusteringService
from app.services.embeddings import EmbeddingService, VectorIndex

Base.metadata.create_all(bind=engine)
SAMPLE = [
    ("RAG Evaluation Benchmarks for Long Context Systems", "We study retrieval augmented generation evaluation with long context models and benchmark disagreement.", "cs.CL"),
    ("Agentic Retrieval for Scientific Discovery", "An agentic workflow decomposes scientific questions and retrieves evidence from paper collections.", "cs.AI"),
    ("Efficient Vision Transformers for Agriculture", "Lightweight vision transformers classify crop stress from remote sensing imagery.", "cs.CV"),
    ("Time Series Foundation Models", "Pretrained sequence models improve forecasting under distribution shift and limited labels.", "cs.LG"),
    ("Contrastive Signal Processing Representations", "Self-supervised embeddings improve signal classification in low-resource settings.", "eess.SP"),
    ("Multimodal Reasoning with Tool Use", "Large multimodal models combine visual inputs, retrieval, and tools for reasoning tasks.", "cs.AI"),
]

with SessionLocal() as db:
    project = ProjectRepository(db).create("Large Language Models")
    papers = PaperRepository(db).add_many(project.id, [
        {
            "arxiv_id": f"sample.{idx}",
            "title": title,
            "abstract": abstract,
            "authors": "Ada Lovelace; Alan Turing",
            "categories": cat,
            "published_at": datetime(2025, min(idx, 12), 1),
            "pdf_url": f"https://arxiv.org/pdf/sample.{idx}",
            "citation_count": idx * 3,
        }
        for idx, (title, abstract, cat) in enumerate(SAMPLE, start=1)
    ])
    texts = [f"{p.title}. {p.abstract}" for p in papers]
    vectors = EmbeddingService().encode(texts)
    VectorIndex().build(project.id, [p.id for p in papers], vectors)
    cluster_rows, assignments, _ = ClusteringService().cluster([p.id for p in papers], texts, vectors)
    ClusterRepository(db).replace(project.id, cluster_rows, assignments)
    ProjectRepository(db).set_status(project, "ready")
    print(f"Seeded project {project.id}: {project.topic}")
