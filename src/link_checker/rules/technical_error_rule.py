from __future__ import annotations

from link_checker.enums import LinkStatus
from link_checker.models import RuleMatch, ValidationContext


class TechnicalErrorRule:
    name = "technical_error"

    def match(self, context: ValidationContext) -> RuleMatch | None:
        if context.http_result.timed_out:
            return None

        error = context.http_result.error
        if error:
            return RuleMatch(LinkStatus.ERRO_TECNICO, self.name, error)
        return None
