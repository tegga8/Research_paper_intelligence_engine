from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.config import get_settings
from app.db import models
from app.db.session import engine

settings = get_settings()
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    description="ArXiv-powered research discovery, clustering, trend analysis, literature reviews, gap finding, recommendations, citation graphs, and RAG.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(router)
