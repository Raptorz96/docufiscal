from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./docufiscal.db"
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    CLAUDE_API_KEY: str = ""
    STORAGE_ROOT: str = "storage/documenti"
    # AI Classification
    AI_PROVIDER: str = "gemini"
    AI_MODEL: str = "gemini-2.5-flash"
    AI_API_KEY: str = ""
    CONFIDENCE_THRESHOLD: float = 0.75
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50 MB in bytes
    ALLOWED_MIME_TYPES: list[str] = Field(
        default=[
            "application/pdf",
            "image/jpeg",
            "image/png",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/msword",
            "application/vnd.ms-excel",
        ]
    )

    model_config = {"env_file": ".env"}


settings = Settings()