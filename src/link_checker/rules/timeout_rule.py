from __future__ import annotations

from link_checker.enums import LinkStatus
from link_checker.models import RuleMatch, ValidationContext


class TimeoutRule:
    name = "timeout_rule"

    def match(self, context: ValidationContext) -> RuleMatch | None:
        if context.http_result.timed_out:
            return RuleMatch(
                LinkStatus.TIMEOUT,
                self.name,
                context.http_result.error or "Timeout",
            )
        return None
