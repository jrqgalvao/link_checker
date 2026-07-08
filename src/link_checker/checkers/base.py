from __future__ import annotations

from typing import Protocol

from link_checker.models import HttpCheckResult


class HttpCheckerProtocol(Protocol):
    def check(self, url: str) -> HttpCheckResult: ...
