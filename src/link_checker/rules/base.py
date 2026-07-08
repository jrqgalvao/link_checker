from __future__ import annotations

from typing import Protocol

from link_checker.models import RuleMatch, ValidationContext


class ValidationRule(Protocol):
    name: str

    def match(self, context: ValidationContext) -> RuleMatch | None: ...
