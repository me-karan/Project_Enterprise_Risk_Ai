"""
Unit tests for AuraRisk application settings.

These tests verify configuration loading, nested environment variables,
secret masking, production safeguards, and cached settings behavior.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from pydantic import ValidationError

from aurarisk.core.settings import (
    DEFAULT_DATABASE_PASSWORD,
    DEFAULT_JWT_SECRET,
    ApplicationEnvironment,
    ApplicationSettings,
    clear_settings_cache,
    get_settings,
)


@pytest.fixture(autouse=True)
def reset_cached_settings() -> Iterator[None]:
    """
    Clear settings before and after every test.

    This prevents one test's environment overrides from leaking into another.
    """

    clear_settings_cache()

    yield

    clear_settings_cache()


def test_default_environment_is_development() -> None:
    """Default settings should support local development."""

    settings = ApplicationSettings(_env_file=None)

    assert settings.environment == ApplicationEnvironment.DEVELOPMENT


def test_nested_environment_variable_overrides_api_port(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nested environment variables should update nested settings."""

    monkeypatch.setenv(
        "AURARISK_API__PORT",
        "9001",
    )

    settings = ApplicationSettings(_env_file=None)

    assert settings.api.port == 9001


def test_invalid_api_port_is_rejected() -> None:
    """Ports outside the valid TCP range must fail validation."""

    with pytest.raises(ValidationError):
        ApplicationSettings(
            _env_file=None,
            api={
                "port": 70000,
            },
        )


def test_boolean_environment_values_are_parsed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """String environment values should become actual booleans."""

    monkeypatch.setenv(
        "AURARISK_DEBUG",
        "true",
    )

    settings = ApplicationSettings(_env_file=None)

    assert settings.debug is True


def test_environment_variable_overrides_dotenv_value(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Operating-system environment variables take priority over .env."""

    temporary_env_file = tmp_path / ".env"

    temporary_env_file.write_text(
        "AURARISK_API__PORT=8001\n",
        encoding="utf-8",
    )

    monkeypatch.setenv(
        "AURARISK_API__PORT",
        "9002",
    )

    settings = ApplicationSettings(_env_file=temporary_env_file)

    assert settings.api.port == 9002


def test_database_password_is_masked() -> None:
    """Sensitive database values must not appear in model representations."""

    raw_password = "sensitive-database-password"

    settings = ApplicationSettings(
        _env_file=None,
        database={
            "password": raw_password,
        },
    )

    assert raw_password not in repr(settings.database)

    assert raw_password not in (settings.model_dump_json())


def test_database_connection_url_is_masked() -> None:
    """The generated database URL should also remain protected."""

    settings = ApplicationSettings(_env_file=None)

    assert DEFAULT_DATABASE_PASSWORD not in str(settings.database.sqlalchemy_url)


def test_hosted_llm_provider_requires_api_key() -> None:
    """Enabled hosted providers must not start without credentials."""

    with pytest.raises(
        ValidationError,
        match="requires an API key",
    ):
        ApplicationSettings(
            _env_file=None,
            llm={
                "enabled": True,
                "provider": "openai",
            },
        )


def test_mock_llm_provider_does_not_require_api_key() -> None:
    """Local mock workflows should work without provider credentials."""

    settings = ApplicationSettings(
        _env_file=None,
        llm={
            "enabled": True,
            "provider": "mock",
        },
    )

    assert settings.llm.api_key is None


def test_short_jwt_secret_is_rejected() -> None:
    """JWT configuration must reject insufficiently long secrets."""

    with pytest.raises(
        ValidationError,
        match="at least 32 characters",
    ):
        ApplicationSettings(
            _env_file=None,
            security={
                "jwt_secret": "too-short",
            },
        )


def test_production_debug_mode_is_rejected() -> None:
    """Production environments must not start with debug enabled."""

    with pytest.raises(
        ValidationError,
        match="Debug mode must be disabled",
    ):
        ApplicationSettings(
            _env_file=None,
            environment=ApplicationEnvironment.PRODUCTION,
            debug=True,
        )


def test_production_default_jwt_secret_is_rejected() -> None:
    """Production environments cannot use the development JWT secret."""

    with pytest.raises(
        ValidationError,
        match="development JWT secret",
    ):
        ApplicationSettings(
            _env_file=None,
            environment=ApplicationEnvironment.PRODUCTION,
            debug=False,
            api={
                "docs_enabled": False,
            },
        )


def test_secure_production_settings_are_accepted() -> None:
    """A correctly configured production environment should validate."""

    settings = ApplicationSettings(
        _env_file=None,
        environment=ApplicationEnvironment.PRODUCTION,
        debug=False,
        api={
            "docs_enabled": False,
        },
        database={
            "password": "separate-production-database-password",
        },
        security={
            "jwt_secret": ("production-jwt-secret-with-more-than-32-characters"),
        },
    )

    assert settings.environment == ApplicationEnvironment.PRODUCTION


def test_safe_summary_excludes_sensitive_values() -> None:
    """Diagnostic output must never include sensitive values."""

    settings = ApplicationSettings(_env_file=None)

    summary = str(settings.safe_summary())

    assert DEFAULT_DATABASE_PASSWORD not in summary
    assert DEFAULT_JWT_SECRET not in summary


def test_settings_are_cached() -> None:
    """Repeated settings requests should return the same object."""

    first_settings = get_settings()

    second_settings = get_settings()

    assert first_settings is second_settings


def test_clearing_cache_reloads_environment_changes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Clearing the cache should allow updated configuration values."""

    first_settings = get_settings()

    monkeypatch.setenv(
        "AURARISK_API__PORT",
        "9100",
    )

    # The existing cached settings remain unchanged.
    assert get_settings() is first_settings

    clear_settings_cache()

    refreshed_settings = get_settings()

    assert refreshed_settings.api.port == 9100
