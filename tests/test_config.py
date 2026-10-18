import pytest

from config import load_settings


def test_load_settings_from_environment(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "15")
    monkeypatch.setenv("LLM_MAX_ATTEMPTS", "2")

    settings = load_settings()

    assert settings.openai_api_key == "test-key"
    assert settings.model == "test-model"
    assert settings.timeout_seconds == 15
    assert settings.max_attempts == 2


def test_missing_api_key_is_rejected(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_MODEL", "test-model")

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        load_settings()


def test_invalid_timeout_is_rejected(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "0")

    with pytest.raises(ValueError, match="must be positive"):
        load_settings()


def test_invalid_attempt_count_is_rejected(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    monkeypatch.setenv("LLM_MAX_ATTEMPTS", "0")

    with pytest.raises(ValueError, match="at least 1"):
        load_settings()
