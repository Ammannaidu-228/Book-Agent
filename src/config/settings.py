"""
Configuration settings for the Lit-Pick backend
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # API Settings
    API_TITLE: str = "Lit-Pick - AI Book Recommendation Engine"
    API_VERSION: str = "1.0.0"
    DEBUG: bool | str = False
    
    # OpenAI Settings
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # Database Settings
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "litpick"
    
    # Vector DB Settings
    CHROMA_PERSIST_DIR: str = str(REPO_ROOT / "chroma_db")
    CHROMA_COLLECTION_NAME: str = "langchain"

    @field_validator("CHROMA_PERSIST_DIR")
    @classmethod
    def resolve_chroma_persist_dir(cls, value: str) -> str:
        path = Path(value)
        if path.is_absolute():
            return str(path)
        return str((REPO_ROOT / path).resolve())
    
    # Performance Settings
    MAX_WORKERS: int = 4
    BATCH_SIZE: int = 8
    CACHE_TTL: int = 3600  # 1 hour
    CONNECTION_POOL_SIZE: int = 20
    RECOMMENDATION_TIMEOUT: int = 25
    ENABLE_EMOTION_CLASSIFICATION: bool = False

    # Emotion Classification Settings
    EMOTION_MODEL: str = "facebook/bart-large-mnli"
    EMOTIONS: list = [
        "joyful", "mysterious", "thrilling", "romantic", "thought-provoking",
        "sad", "humorous", "dark", "inspirational", "intimate"
    ]
    
    # Recommendation Settings
    TOP_K_RESULTS: int = 10
    SIMILARITY_THRESHOLD: float = 0.6
    
    # Optional: Hugging Face Token
    HF_TOKEN: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields from .env


settings = Settings()
