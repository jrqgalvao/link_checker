import pytest

from link_checker.config import Settings


def test_operational_defaults_are_tuned_for_batch_validation() -> None:
    settings = Settings()

    assert settings.max_workers == 24
    assert settings.http_timeout_seconds == 12.0
    assert settings.http_retry_count == 1


def test_rejects_invalid_runtime_configuration(monkeypatch) -> None:
    monkeypatch.setenv("LINK_CHECKER_HTTP_RETRY_COUNT", "-1")

    with pytest.raises(ValueError, match="deve ser maior ou igual a 0"):
        Settings()


def test_rejects_invalid_explicit_worker_count() -> None:
    with pytest.raises(ValueError, match="LINK_CHECKER_MAX_WORKERS"):
        Settings(max_workers=0)
