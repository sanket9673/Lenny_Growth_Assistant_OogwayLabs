from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    PROJECT_NAME: str = "Lenny Growth Assistant"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgrespassword@localhost:5433/lenny_growth"
    )
    SYNC_DATABASE_URL: str = Field(
        default="postgresql+psycopg2://postgres:postgrespassword@localhost:5433/lenny_growth"
    )
    
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIMENSION: int = 384
    
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    ANTHROPIC_API_KEY: str = ""
    GROQ_API_KEY: str = ""

settings = Settings()
