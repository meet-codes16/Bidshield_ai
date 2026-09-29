from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "iProcurement"

    # Database
    DATABASE_URL: str = "sqlite:///./data/iprocurement.db"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # MinIO
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "iprocurement"

    # JWT
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 30
    REFRESH_TOKEN_DAYS: int = 7

    # Groq API
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-20b"

    # LLM
    MOCK_LLM: bool = False

    # Vector DB
    VECTOR_DB_URL: str = ""

    # Upload
    MAX_UPLOAD_SIZE: int = 26214400
    UPLOAD_DIR: str = "data/uploads"
    EXTRACTED_DIR: str = "data/extracted"
    AUDIT_DB: str = "data/audit.db"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # Storage / Services
    STORAGE_MODE: str = "local"
    AUTHORITY_MODE: str = "mock"
    EMBEDDING_MODE: str = "local"
    WORKER_MODE: str = "inline"

    # Environment file
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()