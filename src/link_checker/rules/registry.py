from __future__ import annotations

from collections.abc import Iterable

from link_checker.models import RuleMatch, ValidationContext
from link_checker.rules.base import ValidationRule
from link_checker.rules.event_page_rule import EventPageRule
from link_checker.rules.http_error_rule import HttpErrorRule
from link_checker.rules.support_error_rule import SupportErrorRule
from link_checker.rules.technical_error_rule import TechnicalErrorRule
from link_checker.rules.timeout_rule import TimeoutRule


class RuleRegistry:
    def __init__(self, rules: Iterable[ValidationRule] | None = None) -> None:
        self.rules = (
            list(rules)
            if rules is not None
            else [
                TimeoutRule(),
                TechnicalErrorRule(),
                HttpErrorRule(),
                SupportErrorRule(),
                EventPageRule(),
            ]
        )

    def classify(self, context: ValidationContext) -> RuleMatch | None:
        for rule in self.rules:
            match = rule.match(context)
            if match:
                return match
        return None
