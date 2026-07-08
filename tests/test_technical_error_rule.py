from link_checker.enums import LinkStatus
from link_checker.models import HttpCheckResult, ValidationContext
from link_checker.rules.technical_error_rule import TechnicalErrorRule


def test_technical_error_not_timeout_returns_erro_tecnico() -> None:
    rule = TechnicalErrorRule()
    context = ValidationContext(
        http_result=HttpCheckResult(
            link="https://x.test",
            timed_out=False,
            error="Name resolution failed",
        )
    )
    match = rule.match(context)
    assert match is not None
    assert match.status == LinkStatus.ERRO_TECNICO


def test_technical_error_preserves_evidence() -> None:
    rule = TechnicalErrorRule()
    context = ValidationContext(
        http_result=HttpCheckResult(
            link="https://x.test",
            timed_out=False,
            error="Connection refused",
        )
    )
    match = rule.match(context)
    assert match is not None
    assert match.rule_name == "technical_error"
    assert "Connection refused" in match.evidence


def test_timeout_with_error_returns_none() -> None:
    rule = TechnicalErrorRule()
    context = ValidationContext(
        http_result=HttpCheckResult(
            link="https://x.test",
            timed_out=True,
            error="Timeout apos 30 segundos",
        )
    )
    match = rule.match(context)
    assert match is None


def test_no_error_returns_none() -> None:
    rule = TechnicalErrorRule()
    context = ValidationContext(
        http_result=HttpCheckResult(link="https://x.test", status_code=200, timed_out=False)
    )
    match = rule.match(context)
    assert match is None


def test_http_error_with_status_code_no_technical_error_returns_none() -> None:
    rule = TechnicalErrorRule()
    context = ValidationContext(
        http_result=HttpCheckResult(link="https://x.test", status_code=500, timed_out=False)
    )
    match = rule.match(context)
    assert match is None
