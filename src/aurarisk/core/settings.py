"""
Central application settings for AuraRisk.

Configuration is loaded from:

1. Explicit constructor arguments.
2. Operating-system environment variables.
3. The project-level .env file.
4. Defaults declared in these models.

The settings object is cached so application components share one validated
configuration instance.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, Self
from urllib.parse import quote

from pydantic import (
    BaseModel,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from aurarisk import __version__


# settings.py is located at:
#
# project_root/src/aurarisk/core/settings.py
#
# Moving three levels upward from the file's parent resolves the repository
# root without depending on the terminal's current working directory.
PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"

DEFAULT_DATABASE_PASSWORD = "local-development-password-change-me"

DEFAULT_JWT_SECRET = "development-jwt-secret-change-before-production-32"


class ApplicationEnvironment(StrEnum):
    """Deployment environment recognized by the application."""

    DEVELOPMENT = "development"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class APISettings(BaseModel):
    """HTTP API configuration."""

    host: str = "127.0.0.1"

    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="TCP port used by the FastAPI application.",
    )

    docs_enabled: bool = True

    allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:8501",
        ],
        description="Frontend origins permitted to call the API.",
    )


class DatabaseSettings(BaseModel):
    """PostgreSQL connection and connection-pool configuration."""

    host: str = "localhost"

    port: int = Field(
        default=5432,
        ge=1,
        le=65535,
    )

    name: str = "aurarisk"

    username: str = "aurarisk_user"

    # SecretStr prevents the raw password from appearing in normal repr()
    # output and Pydantic's default JSON serialization.
    password: SecretStr = Field(default_factory=lambda: SecretStr(DEFAULT_DATABASE_PASSWORD))

    pool_size: int = Field(
        default=5,
        ge=1,
        le=100,
    )

    max_overflow: int = Field(
        default=10,
        ge=0,
        le=100,
    )

    @property
    def sqlalchemy_url(self) -> SecretStr:
        """
        Build a PostgreSQL connection URL without exposing the password.

        The return value is also a SecretStr, so accidental logging prints
        masked output rather than the raw connection string.
        """

        safe_username = quote(
            self.username,
            safe="",
        )

        safe_password = quote(
            self.password.get_secret_value(),
            safe="",
        )

        connection_url = (
            f"postgresql+psycopg://"
            f"{safe_username}:{safe_password}"
            f"@{self.host}:{self.port}/{self.name}"
        )

        return SecretStr(connection_url)


class RedisSettings(BaseModel):
    """Redis configuration for caching and workflow state."""

    enabled: bool = False

    host: str = "localhost"

    port: int = Field(
        default=6379,
        ge=1,
        le=65535,
    )

    database: int = Field(
        default=0,
        ge=0,
        le=15,
    )

    password: SecretStr | None = None


class KafkaSettings(BaseModel):
    """Kafka configuration for transaction and case events."""

    enabled: bool = False

    bootstrap_servers: str = "localhost:9092"

    transaction_topic: str = "aurarisk.transactions"

    case_topic: str = "aurarisk.cases"


class LLMSettings(BaseModel):
    """Model-provider settings and per-case cost limits."""

    enabled: bool = False

    provider: Literal[
        "mock",
        "openai",
        "anthropic",
        "local",
    ] = "mock"

    model: str = "mock-investigation-model"

    api_key: SecretStr | None = None

    timeout_seconds: int = Field(
        default=30,
        ge=1,
        le=300,
    )

    max_tokens: int = Field(
        default=2000,
        ge=1,
        le=100000,
    )

    max_cost_per_case_usd: float = Field(
        default=0.15,
        gt=0,
    )

    @model_validator(mode="after")
    def validate_provider_credentials(self) -> Self:
        """
        Require credentials only when a hosted provider is enabled.

        Mock and local providers can operate without an external API key.
        """

        if not self.enabled:
            return self

        if self.provider in {"mock", "local"}:
            return self

        if self.api_key is None:
            raise ValueError(f"LLM provider {self.provider!r} requires an API key.")

        if not self.api_key.get_secret_value().strip():
            raise ValueError(f"LLM provider {self.provider!r} requires a non-empty API key.")

        return self


class SecuritySettings(BaseModel):
    """Authentication, token, and sensitive-data protection settings."""

    require_authentication: bool = True

    jwt_secret: SecretStr = Field(default_factory=lambda: SecretStr(DEFAULT_JWT_SECRET))

    jwt_algorithm: Literal["HS256"] = "HS256"

    access_token_expire_minutes: int = Field(
        default=60,
        ge=1,
        le=1440,
    )

    mask_sensitive_data: bool = True

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret_length(
        cls,
        value: SecretStr,
    ) -> SecretStr:
        """Reject secrets that are too short for the configured JWT policy."""

        if len(value.get_secret_value()) < 32:
            raise ValueError("JWT secret must contain at least 32 characters.")

        return value


class LoggingSettings(BaseModel):
    """Application logging configuration."""

    level: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = "INFO"

    json_output: bool = False

    redact_sensitive_fields: bool = True


class ObservabilitySettings(BaseModel):
    """Metrics and distributed-tracing configuration."""

    service_name: str = "aurarisk"

    metrics_enabled: bool = True

    trace_export_enabled: bool = False

    otlp_endpoint: str = "http://localhost:4317"


def resolve_product_docs_directory() -> Path:
    """
    Resolve whichever product-document directory already exists.

    Earlier project setup may have used either:

        docs/product/

    or:

        docs/products/

    This keeps both existing layouts compatible.
    """

    candidates = (
        PROJECT_ROOT / "docs" / "products",
        PROJECT_ROOT / "docs" / "product",
    )

    for candidate in candidates:
        if candidate.is_dir():
            return candidate

    # Use the current project's preferred name when neither exists yet.
    return PROJECT_ROOT / "docs" / "products"


class PathSettings(BaseModel):
    """Repository paths referenced by policies and evaluation code."""

    project_root: Path = Field(default_factory=lambda: PROJECT_ROOT)

    policy_directory: Path = Field(default_factory=lambda: PROJECT_ROOT / "config" / "policies")

    release_gates_path: Path = Field(
        default_factory=lambda: PROJECT_ROOT / "config" / "quality" / "release_gates.yaml"
    )

    product_docs_directory: Path = Field(default_factory=resolve_product_docs_directory)


class ApplicationSettings(BaseSettings):
    """
    Top-level application settings.

    Examples:

        AURARISK_ENVIRONMENT=development
        AURARISK_API__PORT=8000
        AURARISK_DATABASE__HOST=localhost

    Environment variables override values defined in the .env file.
    """

    model_config = SettingsConfigDict(
        env_prefix="AURARISK_",
        env_nested_delimiter="__",
        env_file=DEFAULT_ENV_FILE,
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
    )

    app_name: str = "AuraRisk"

    version: str = __version__

    environment: ApplicationEnvironment = ApplicationEnvironment.DEVELOPMENT

    debug: bool = False

    api: APISettings = Field(default_factory=APISettings)

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)

    redis: RedisSettings = Field(default_factory=RedisSettings)

    kafka: KafkaSettings = Field(default_factory=KafkaSettings)

    llm: LLMSettings = Field(default_factory=LLMSettings)

    security: SecuritySettings = Field(default_factory=SecuritySettings)

    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)

    paths: PathSettings = Field(default_factory=PathSettings)

    @model_validator(mode="after")
    def validate_production_security(self) -> Self:
        """
        Fail startup when production uses insecure development settings.

        Development defaults are convenient locally but cannot be accepted
        for a production environment.
        """

        if self.environment != ApplicationEnvironment.PRODUCTION:
            return self

        if self.debug:
            raise ValueError("Debug mode must be disabled in production.")

        if self.api.docs_enabled:
            raise ValueError("Interactive API documentation must be disabled in production.")

        if not self.security.require_authentication:
            raise ValueError("Authentication must be enabled in production.")

        if not self.security.mask_sensitive_data:
            raise ValueError("Sensitive-data masking must be enabled in production.")

        if not self.logging.redact_sensitive_fields:
            raise ValueError("Sensitive-field log redaction must be enabled in production.")

        if self.security.jwt_secret.get_secret_value() == DEFAULT_JWT_SECRET:
            raise ValueError("The development JWT secret cannot be used in production.")

        if self.database.password.get_secret_value() == DEFAULT_DATABASE_PASSWORD:
            raise ValueError("The development database password cannot be used in production.")

        if "*" in self.api.allowed_origins:
            raise ValueError("Wildcard CORS origins are not allowed in production.")

        return self

    def safe_summary(self) -> dict[str, Any]:
        """
        Return operational configuration without credentials.

        This method is safe for controlled startup diagnostics because it
        deliberately excludes database passwords, API keys, and JWT secrets.
        """

        return {
            "app_name": self.app_name,
            "version": self.version,
            "environment": self.environment.value,
            "debug": self.debug,
            "api": {
                "host": self.api.host,
                "port": self.api.port,
                "docs_enabled": self.api.docs_enabled,
            },
            "database": {
                "host": self.database.host,
                "port": self.database.port,
                "name": self.database.name,
                "pool_size": self.database.pool_size,
            },
            "redis": {
                "enabled": self.redis.enabled,
                "host": self.redis.host,
                "port": self.redis.port,
            },
            "kafka": {
                "enabled": self.kafka.enabled,
                "bootstrap_servers": self.kafka.bootstrap_servers,
            },
            "llm": {
                "enabled": self.llm.enabled,
                "provider": self.llm.provider,
                "model": self.llm.model,
            },
            "logging": {
                "level": self.logging.level,
                "json_output": self.logging.json_output,
            },
            "observability": {
                "service_name": self.observability.service_name,
                "metrics_enabled": self.observability.metrics_enabled,
                "trace_export_enabled": (self.observability.trace_export_enabled),
            },
        }


@lru_cache(maxsize=1)
def get_settings() -> ApplicationSettings:
    """
    Load and cache the validated application settings.

    FastAPI, model services, tools, and workers should call this function
    instead of constructing their own settings instances.
    """

    return ApplicationSettings()


def clear_settings_cache() -> None:
    """
    Clear cached settings.

    This is primarily useful in tests that modify environment variables.
    """

    get_settings.cache_clear()
