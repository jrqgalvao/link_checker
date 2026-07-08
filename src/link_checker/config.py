from __future__ import annotations

import os
from dataclasses import dataclass
from functools import cache
from pathlib import Path

_ENV_FILE = ".env"


@dataclass(frozen=True)
class Settings:
    http_timeout_seconds: float = 12.0
    http_retry_count: int = 1
    user_agent: str = "link-checker/0.1"
    max_redirects: int = 10
    max_workers: int = 24
    reports_dir: Path = Path("reports")
    debug: bool = False

    def __init__(
        self,
        *,
        http_timeout_seconds: float | None = None,
        http_retry_count: int | None = None,
        user_agent: str | None = None,
        max_redirects: int | None = None,
        max_workers: int | None = None,
        reports_dir: Path | str | None = None,
        debug: bool | None = None,
    ) -> None:
        object.__setattr__(
            self,
            "http_timeout_seconds",
            _env_float("LINK_CHECKER_HTTP_TIMEOUT_SECONDS", http_timeout_seconds, 12.0),
        )
        object.__setattr__(
            self,
            "http_retry_count",
            _env_int("LINK_CHECKER_HTTP_RETRY_COUNT", http_retry_count, 1),
        )
        object.__setattr__(
            self,
            "user_agent",
            user_agent or _setting_value("LINK_CHECKER_USER_AGENT") or "link-checker/0.1",
        )
        object.__setattr__(
            self,
            "max_redirects",
            _env_int("LINK_CHECKER_MAX_REDIRECTS", max_redirects, 10),
        )
        object.__setattr__(
            self,
            "max_workers",
            _env_int("LINK_CHECKER_MAX_WORKERS", max_workers, 24),
        )
        object.__setattr__(
            self,
            "reports_dir",
            Path(reports_dir or _setting_value("LINK_CHECKER_REPORTS_DIR") or "reports"),
        )
        object.__setattr__(self, "debug", _env_bool("LINK_CHECKER_DEBUG", debug, False))


def _env_int(name: str, explicit: int | None, default: int) -> int:
    if explicit is not None:
        return explicit
    value = _setting_value(name)
    return int(value) if value else default


def _env_float(name: str, explicit: float | None, default: float) -> float:
    if explicit is not None:
        return explicit
    value = _setting_value(name)
    return float(value) if value else default


def _env_bool(name: str, explicit: bool | None, default: bool) -> bool:
    if explicit is not None:
        return explicit
    value = _setting_value(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "sim", "on"}


def _setting_value(name: str) -> str | None:
    return os.getenv(name) or _env_file_values().get(name)


@cache
def _env_file_values() -> dict[str, str]:
    path = Path(_ENV_FILE)
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        clean = line.strip()
        if not clean or clean.startswith("#") or "=" not in clean:
            continue
        key, value = clean.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values
