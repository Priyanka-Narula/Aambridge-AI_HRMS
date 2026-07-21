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
    # Default to a currently available Inference Providers chat model.
    # meta-llama/Meta-Llama-3-8B-Instruct is no longer supported for many accounts.
    HF_MODEL: str = "mistralai/Mistral-7B-Instruct-v0.3"
    HF_MODEL_FALLBACKS: str = (
        "mistralai/Mistral-Nemo-Instruct-2407,"
        "HuggingFaceH4/zephyr-7b-beta,"
        "Qwen/Qwen2.5-7B-Instruct"
    )
    HF_PROVIDER: str = "auto"
    HF_MAX_TOKENS: int = 2048
    HF_TIMEOUT_SECONDS: float = 120.0

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    BOOTSTRAP_OWNER_EMAIL: str = "owner@aambridge.ai"
    BOOTSTRAP_OWNER_PASSWORD: str | None = None
    BOOTSTRAP_OWNER_FIRST_NAME: str = "Platform"
    BOOTSTRAP_OWNER_LAST_NAME: str = "Owner"

    OFFICE_TIMEZONE: str = "Asia/Dubai"
    CHECKIN_EXPECTED: str = "09:00"
    CHECKOUT_EXPECTED: str = "18:30"
    LATE_THRESHOLD: str = "09:15"


settings = Settings()
