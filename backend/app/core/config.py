from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./docufiscal.db"
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    CLAUDE_API_KEY: str = ""
    STORAGE_ROOT: str = "storage/documenti"

    model_config = {"env_file": ".env"}


settings = Settings()