from __future__ import annotations

import socket
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

from link_checker.models import HttpCheckResult

_MAX_RESPONSE_TEXT_CHARS = 100_000
_RETRYABLE_STATUS_CODES = {429, 502, 503, 504}
_DEFAULT_REDIRECT_LIMIT = 10


class _LimitedRedirectHandler(HTTPRedirectHandler):
    def __init__(self, max_redirections: int) -> None:
        super().__init__()
        self.max_redirections = max_redirections


class HttpChecker:
    def __init__(
        self,
        *,
        timeout_seconds: float,
        user_agent: str,
        max_redirects: int,
        retry_count: int = 0,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds deve ser maior que zero")
        if max_redirects < 0:
            raise ValueError("max_redirects deve ser maior ou igual a zero")
        if retry_count < 0:
            raise ValueError("retry_count deve ser maior ou igual a zero")
        self.timeout_seconds = timeout_seconds
        self.user_agent = user_agent
        self.max_redirects = max_redirects
        self.retry_count = retry_count
        self._opener = (
            None
            if max_redirects == _DEFAULT_REDIRECT_LIMIT
            else build_opener(_LimitedRedirectHandler(max_redirects))
        )

    def check(self, url: str) -> HttpCheckResult:
        started = perf_counter()
        clean_url = url.strip()
        if not clean_url:
            return HttpCheckResult(link=url, error="URL vazia", timed_out=False)
        if urlparse(clean_url).scheme not in {"http", "https"}:
            return HttpCheckResult(
                link=url,
                error="URL sem protocolo http/https",
                timed_out=False,
            )

        last_result: HttpCheckResult | None = None
        for attempt in range(self.retry_count + 1):
            result = self._check_once(url, clean_url, started)
            if not _should_retry(result) or attempt >= self.retry_count:
                return result
            last_result = result

        return last_result or HttpCheckResult(link=url, error="Erro tecnico desconhecido")

    def _check_once(self, original_url: str, clean_url: str, started: float) -> HttpCheckResult:
        try:
            request = Request(clean_url, headers={"User-Agent": self.user_agent}, method="GET")
            open_url = urlopen if self._opener is None else self._opener.open
            with open_url(request, timeout=self.timeout_seconds) as response:
                response_text = _read_limited_text(response)
                return HttpCheckResult(
                    link=original_url,
                    status_code=response.status,
                    final_url=response.geturl(),
                    redirect_history=(),
                    response_time_seconds=perf_counter() - started,
                    response_text=response_text,
                )
        except HTTPError as exc:
            response_text = _read_limited_text(exc)
            return HttpCheckResult(
                link=original_url,
                status_code=exc.code,
                final_url=exc.geturl(),
                redirect_history=(),
                response_time_seconds=perf_counter() - started,
                response_text=response_text,
            )
        except TimeoutError:
            return _timeout_result(original_url, started, self.timeout_seconds)
        except URLError as exc:
            if isinstance(exc.reason, (TimeoutError, socket.timeout)):
                return _timeout_result(original_url, started, self.timeout_seconds)
            return HttpCheckResult(
                link=original_url,
                response_time_seconds=perf_counter() - started,
                error=f"HTTP error: {exc}",
                timed_out=False,
            )
        except OSError as exc:
            return HttpCheckResult(
                link=original_url,
                response_time_seconds=perf_counter() - started,
                error=f"HTTP error: {exc}",
                timed_out=False,
            )
        except (TypeError, ValueError) as exc:
            return HttpCheckResult(
                link=original_url,
                response_time_seconds=perf_counter() - started,
                error=f"URL invalida: {exc}",
                timed_out=False,
            )


def _timeout_result(original_url: str, started: float, timeout_seconds: float) -> HttpCheckResult:
    return HttpCheckResult(
        link=original_url,
        response_time_seconds=perf_counter() - started,
        error=f"Timeout apos {timeout_seconds} segundos",
        timed_out=True,
    )


def _read_limited_text(response) -> str:
    raw = response.read(_MAX_RESPONSE_TEXT_CHARS)
    encoding = response.headers.get_content_charset() if response.headers else None
    return raw.decode(encoding or "utf-8", errors="replace")


def _should_retry(result: HttpCheckResult) -> bool:
    if result.timed_out or result.error:
        return True
    return result.status_code in _RETRYABLE_STATUS_CODES
