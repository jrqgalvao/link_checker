from __future__ import annotations

from link_checker.enums import LinkStatus
from link_checker.models import RuleMatch, ValidationContext


class HttpErrorRule:
    name = "http_error"

    def match(self, context: ValidationContext) -> RuleMatch | None:
        if context.http_result.timed_out:
            return None

        status_code = context.http_result.status_code
        if status_code is None:
            return None

        if status_code == 404:
            return RuleMatch(LinkStatus.MORTO_404, self.name, "Status HTTP 404")
        if 400 <= status_code <= 599:
            return RuleMatch(LinkStatus.ERRO_HTTP, self.name, f"Status HTTP {status_code}")
        return None
