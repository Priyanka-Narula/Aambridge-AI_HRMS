from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql://hrms:hrms@localhost:5433/hrms"
    DB_ECHO: bool = False

    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "hrms"
    MINIO_SECRET_KEY: str = "hrms_minio_secret"
    MINIO_BUCKET: str = "hrms-cvs"
    MINIO_SECURE: bool = False
    GOOGLE_DRIVE_SYNC_DIR: str | None = None

    HF_API_TOKEN: str | None = None
    HF_MODEL: str = "meta-llama/Meta-Llama-3-8B-Instruct"
    HF_MAX_TOKENS: int = 2048


settings = Settings()
