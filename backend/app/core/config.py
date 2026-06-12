from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Research Paper Intelligence Engine"
    database_url: str = "sqlite:///./research.db"
    faiss_index_dir: str = ".faiss"
    cors_origins: str = "http://localhost:3000"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    arxiv_base_url: str = "https://export.arxiv.org/api/query"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
