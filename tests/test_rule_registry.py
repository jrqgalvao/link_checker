from link_checker.enums import LinkStatus
from link_checker.models import HttpCheckResult, RuleMatch, ValidationContext
from link_checker.rules.base import ValidationRule
from link_checker.rules.event_page_rule import EventPageRule
from link_checker.rules.http_error_rule import HttpErrorRule
from link_checker.rules.registry import RuleRegistry
from link_checker.rules.support_error_rule import SupportErrorRule
from link_checker.rules.technical_error_rule import TechnicalErrorRule
from link_checker.rules.timeout_rule import TimeoutRule


class FirstRule(ValidationRule):
    name = "first"

    def match(self, context: ValidationContext) -> RuleMatch | None:
        return RuleMatch(status=LinkStatus.OK, rule_name=self.name, evidence="first")


class SecondRule(ValidationRule):
    name = "second"

    def match(self, context: ValidationContext) -> RuleMatch | None:
        return RuleMatch(status=LinkStatus.ERRO_HTTP, rule_name=self.name, evidence="second")


def test_rule_registry_uses_first_matching_rule() -> None:
    match = RuleRegistry([FirstRule(), SecondRule()]).classify(
        ValidationContext(http_result=HttpCheckResult(link="https://x.test"))
    )

    assert match is not None
    assert match.rule_name == "first"


def test_rule_registry_default_order_is_explicit() -> None:
    registry = RuleRegistry()

    assert [type(rule) for rule in registry.rules] == [
        TimeoutRule,
        TechnicalErrorRule,
        HttpErrorRule,
        SupportErrorRule,
        EventPageRule,
    ]
