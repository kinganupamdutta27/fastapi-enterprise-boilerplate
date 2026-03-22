"""
Centralised application configuration using pydantic-settings.

All settings are loaded from environment variables or a .env file.
Grouped logically so each team/module only depends on the section it needs.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────────────
    app_name: str = "FastAPI Production Template"
    app_version: str = "1.0.0"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_env: str = "development"  # development | staging | production
    app_debug: bool = False
    app_log_level: str = "INFO"
    cors_origins: str = "*"

    # ── Database (PostgreSQL via PgBouncer) ─────────────────────────────
    database_host: str = "localhost"
    database_port: int = 6432
    database_user: str = "app_user"
    database_password: str = "app_secret"
    database_name: str = "app_db"
    database_direct_port: int = 5432

    # ── Connection Pool (small app-side pool; PgBouncer multiplexes) ───
    db_pool_min_size: int = 2
    db_pool_max_size: int = 10
    db_pool_max_inactive_lifetime: float = 300.0
    db_command_timeout: float = 60.0  # asyncpg driver-level timeout (seconds)
    db_statement_timeout: int = 5_000  # PostgreSQL server-side (ms)
    db_idle_in_transaction_timeout: int = 10_000  # PostgreSQL server-side (ms)

    # ── Circuit Breaker ────────────────────────────────────────────────
    cb_fail_max: int = 5
    cb_timeout_duration: int = 30  # seconds before half-open

    # ── Retry ──────────────────────────────────────────────────────────
    db_retry_attempts: int = 3

    # ── Redis ──────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── RabbitMQ ───────────────────────────────────────────────────────
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    rabbitmq_prefetch_count: int = 10

    # ── Kafka ──────────────────────────────────────────────────────────
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_consumer_group: str = "app-consumer-group"

    # ── Elasticsearch / ELK ────────────────────────────────────────────
    elasticsearch_url: str = "http://localhost:9200"

    # ── GenAI / LLM ───────────────────────────────────────────────────
    openai_api_key: str = ""
    llm_model_name: str = "gpt-4o"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 4096
    langchain_tracing_v2: bool = False
    langsmith_api_key: str = ""

    # ── Security ───────────────────────────────────────────────────────
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 30
    api_key_header: str = "X-API-Key"

    @property
    def dsn(self) -> str:
        return (
            f"postgresql://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )

    @property
    def direct_dsn(self) -> str:
        return (
            f"postgresql://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_direct_port}/{self.database_name}"
        )

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
