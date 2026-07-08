from link_checker.config import Settings


def test_operational_defaults_are_tuned_for_batch_validation() -> None:
    settings = Settings()

    assert settings.max_workers == 24
    assert settings.http_timeout_seconds == 12.0
    assert settings.http_retry_count == 1
