from __future__ import annotations

import socket
from email.message import Message
from unittest import mock
from urllib.error import HTTPError, URLError

import pytest

from link_checker.checkers.http_checker import HttpChecker
from link_checker.models import HttpCheckResult


@pytest.fixture
def checker() -> HttpChecker:
    return HttpChecker(timeout_seconds=30.0, user_agent="test-agent", max_redirects=5)


class FakeResponse:
    def __init__(
        self,
        *,
        text: str = "OK",
        status: int = 200,
        url: str = "https://x.test",
    ) -> None:
        self.status = status
        self._url = url
        self._body = text.encode()
        self.headers = Message()
        self.headers.set_param("charset", "utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self, size: int = -1) -> bytes:
        return self._body if size < 0 else self._body[:size]

    def geturl(self) -> str:
        return self._url


def test_uses_configured_timeout() -> None:
    checker = HttpChecker(timeout_seconds=30.0, user_agent="test", max_redirects=5)
    assert checker.timeout_seconds == 30.0


def test_empty_url_returns_controlled_error(checker: HttpChecker) -> None:
    result = checker.check("")

    assert result.error == "URL vazia"
    assert result.timed_out is False


def test_url_without_protocol_returns_controlled_error(checker: HttpChecker) -> None:
    result = checker.check("example.com/link")

    assert result.error == "URL sem protocolo http/https"
    assert result.timed_out is False


def test_timeout_exception_returns_controlled_result(checker: HttpChecker) -> None:
    with mock.patch("link_checker.checkers.http_checker.urlopen", side_effect=socket.timeout):
        result = checker.check("https://x.test")
    assert isinstance(result, HttpCheckResult)


def test_timeout_sets_timed_out_true(checker: HttpChecker) -> None:
    with mock.patch("link_checker.checkers.http_checker.urlopen", side_effect=socket.timeout):
        result = checker.check("https://x.test")
    assert result.timed_out is True


def test_timeout_fills_technical_error(checker: HttpChecker) -> None:
    with mock.patch("link_checker.checkers.http_checker.urlopen", side_effect=socket.timeout):
        result = checker.check("https://x.test")
    assert result.error is not None
    assert "Timeout" in result.error


def test_timeout_does_not_raise(checker: HttpChecker) -> None:
    with mock.patch("link_checker.checkers.http_checker.urlopen", side_effect=socket.timeout):
        result = checker.check("https://x.test")
    assert isinstance(result, HttpCheckResult)


def test_http_error_sets_timed_out_false(checker: HttpChecker) -> None:
    with mock.patch(
        "link_checker.checkers.http_checker.urlopen",
        side_effect=URLError("connection error"),
    ):
        result = checker.check("https://x.test")
    assert result.timed_out is False


def test_http_error_fills_technical_error(checker: HttpChecker) -> None:
    with mock.patch(
        "link_checker.checkers.http_checker.urlopen",
        side_effect=URLError("connection error"),
    ):
        result = checker.check("https://x.test")
    assert result.error is not None
    assert result.timed_out is False


def test_normal_response_sets_timed_out_false(checker: HttpChecker) -> None:
    with mock.patch(
        "link_checker.checkers.http_checker.urlopen",
        return_value=FakeResponse(text="OK"),
    ):
        result = checker.check("https://x.test")

    assert result.timed_out is False
    assert result.status_code == 200
    assert result.error is None


def test_large_response_text_is_truncated(checker: HttpChecker) -> None:
    with mock.patch(
        "link_checker.checkers.http_checker.urlopen",
        return_value=FakeResponse(text="x" * 200_000),
    ):
        result = checker.check("https://x.test")

    assert result.response_text is not None
    assert len(result.response_text) == 100_000


def test_retries_timeout_then_returns_success() -> None:
    checker = HttpChecker(
        timeout_seconds=30.0,
        user_agent="test-agent",
        max_redirects=5,
        retry_count=1,
    )

    with mock.patch(
        "link_checker.checkers.http_checker.urlopen",
        side_effect=[socket.timeout, FakeResponse(text="OK")],
    ):
        result = checker.check("https://x.test")

    assert result.status_code == 200
    assert result.error is None


def test_retries_429_then_returns_success() -> None:
    checker = HttpChecker(
        timeout_seconds=30.0,
        user_agent="test-agent",
        max_redirects=5,
        retry_count=1,
    )
    rate_limit = HTTPError("https://x.test", 429, "rate limit", {}, None)
    rate_limit.headers = Message()
    rate_limit.fp = None

    with mock.patch(
        "link_checker.checkers.http_checker.urlopen",
        side_effect=[rate_limit, FakeResponse(status=200, text="OK")],
    ):
        result = checker.check("https://x.test")

    assert result.status_code == 200
    assert result.error is None
