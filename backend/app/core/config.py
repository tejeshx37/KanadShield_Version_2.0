"""Typed application configuration. Every environment-dependent value lives
here, sourced from environment variables — never hardcoded at call sites."""
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    APP_NAME: str = "KanadShield"
    ENVIRONMENT: Literal["development", "staging", "production", "test"] = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/kanadshield"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # --- Redis / Celery ---
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # --- Auth ---
    JWT_SECRET_KEY: str = Field(default="change-me-in-env", repr=False)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    # --- AI providers ---
    AI_PROVIDER: Literal["ollama", "openai_compatible"] = "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_LLM_MODEL: str = "llama3.1"
    OPENAI_COMPATIBLE_BASE_URL: str | None = None
    OPENAI_COMPATIBLE_API_KEY: str | None = Field(default=None, repr=False)
    OPENAI_COMPATIBLE_LLM_MODEL: str | None = None

    EMBEDDING_PROVIDER: Literal["local", "openai_compatible"] = "local"
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-m3"
    EMBEDDING_DIMENSIONS: int = 1024

    OCR_PROVIDER: Literal["tesseract", "cloud"] = "tesseract"
    SPEECH_PROVIDER: Literal["faster_whisper"] = "faster_whisper"
    WHISPER_MODEL_SIZE: str = "small"

    LLM_REQUEST_TIMEOUT_SECONDS: int = 60
    LLM_MAX_RETRIES: int = 2

    # --- Multilingual ---
    SUPPORTED_LANGUAGES: str = "en,gu,hi"
    DEFAULT_LANGUAGE: str = "en"

    @property
    def supported_languages(self) -> list[str]:
        return [x.strip() for x in self.SUPPORTED_LANGUAGES.split(",") if x.strip()]

    # --- Search ranking weights (config, never inline literals) ---
    SEARCH_WEIGHT_LEXICAL: float = 0.35
    SEARCH_WEIGHT_SEMANTIC: float = 0.40
    SEARCH_WEIGHT_METADATA: float = 0.10
    SEARCH_WEIGHT_AUTHORITY: float = 0.10
    SEARCH_WEIGHT_FRESHNESS: float = 0.05
    SEARCH_DEFAULT_PAGE_SIZE: int = 20
    SEARCH_MAX_PAGE_SIZE: int = 100

    # --- Authority ranking (source_type -> weight, higher = more authoritative) ---
    AUTHORITY_WEIGHTS_JSON: str = (
        '{"SUPREME_COURT_JUDGMENT": 1.0, "HIGH_COURT_JUDGMENT": 0.85, "ACT": 0.85,'
        ' "STATUTE": 0.85, "GAZETTE": 0.65, "NOTIFICATION": 0.55, "GR": 0.5,'
        ' "CIRCULAR": 0.4, "ORDER": 0.4, "SCHEME": 0.4, "GUIDELINE": 0.35, "OTHER": 0.2}'
    )

    # --- RAG ---
    RAG_TOP_K_RETRIEVAL: int = 20
    RAG_TOP_K_CONTEXT: int = 6
    RAG_MIN_RELEVANCE_SCORE: float = 0.35
    RAG_CHUNK_TARGET_TOKENS: int = 500
    RAG_CHUNK_OVERLAP_TOKENS: int = 50

    # --- Citizen data / DigiLocker ---
    DIGILOCKER_ENABLED: bool = False
    DIGILOCKER_CLIENT_ID: str | None = None
    DIGILOCKER_CLIENT_SECRET: str | None = Field(default=None, repr=False)
    DIGILOCKER_BASE_URL: str = "https://api.digitallocker.gov.in"
    DIGILOCKER_REDIRECT_URI: str | None = None

    # --- Ingestion ---
    INGESTION_USER_AGENT: str = "KanadShieldBot/1.0 (+legal-intelligence-platform)"
    INGESTION_REQUEST_TIMEOUT_SECONDS: int = 30
    INGESTION_MAX_RETRIES: int = 3
    INGESTION_RETRY_BACKOFF_SECONDS: float = 2.0
    ENABLED_INGESTION_SOURCES: str = "SOURCE_INDIA_CODE,SOURCE_EGAZETTE,SOURCE_GUJARAT_GR"
    SOURCE_INDIA_CODE_BASE_URL: str = "https://www.indiacode.nic.in"
    SOURCE_EGAZETTE_BASE_URL: str = "https://egazette.gov.in"
    SOURCE_GUJARAT_GR_BASE_URL: str = "https://gr.gujarat.gov.in"

    @property
    def enabled_ingestion_sources(self) -> list[str]:
        return [x.strip() for x in self.ENABLED_INGESTION_SOURCES.split(",") if x.strip()]

    # --- Analytics ---
    ANALYTICS_TRENDING_WINDOW_DAYS: int = 7
    ANALYTICS_MATERIALIZED_VIEW_REFRESH_MINUTES: int = 60

    # --- Rate limiting ---
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_AI: str = "20/minute"
    RATE_LIMIT_AUTH: str = "10/minute"

    # --- CORS / Security headers ---
    CORS_ALLOWED_ORIGINS: str = "http://localhost:5173"
    CSP_HEADER_VALUE: str = "default-src 'self'; frame-ancestors 'none'"
    X_FRAME_OPTIONS: str = "DENY"

    @property
    def cors_allowed_origins(self) -> list[str]:
        return [x.strip() for x in self.CORS_ALLOWED_ORIGINS.split(",") if x.strip()]

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def _warn_default_secret(cls, v: str) -> str:
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
