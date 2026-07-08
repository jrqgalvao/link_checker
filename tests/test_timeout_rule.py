from link_checker.enums import LinkStatus
from link_checker.models import HttpCheckResult, ValidationContext
from link_checker.rules.timeout_rule import TimeoutRule


def test_timeout_rule_returns_timeout_when_timed_out() -> None:
    rule = TimeoutRule()
    context = ValidationContext(
        http_result=HttpCheckResult(link="https://x.test", timed_out=True, error="Timeout")
    )
    match = rule.match(context)
    assert match is not None
    assert match.status == LinkStatus.TIMEOUT
    assert match.rule_name == "timeout_rule"


def test_timeout_rule_returns_none_when_no_timeout() -> None:
    rule = TimeoutRule()
    context = ValidationContext(
        http_result=HttpCheckResult(link="https://x.test", status_code=200, timed_out=False)
    )
    match = rule.match(context)
    assert match is None


def test_timeout_rule_returns_none_when_timed_out_false_with_error() -> None:
    rule = TimeoutRule()
    context = ValidationContext(
        http_result=HttpCheckResult(
            link="https://x.test",
            timed_out=False,
            error="HTTP error: connection refused",
        )
    )
    match = rule.match(context)
    assert match is None
