from link_checker.enums import LinkStatus
from link_checker.models import HttpCheckResult, ValidationContext
from link_checker.rules.http_error_rule import HttpErrorRule


def test_404_returns_morto_404() -> None:
    result = HttpErrorRule().match(
        ValidationContext(http_result=HttpCheckResult(link="https://x.test", status_code=404))
    )
    assert result is not None
    assert result.status == LinkStatus.MORTO_404


def test_400_returns_http_error() -> None:
    result = HttpErrorRule().match(
        ValidationContext(http_result=HttpCheckResult(link="https://x.test", status_code=400))
    )
    assert result is not None
    assert result.status == LinkStatus.ERRO_HTTP


def test_403_returns_http_error() -> None:
    result = HttpErrorRule().match(
        ValidationContext(http_result=HttpCheckResult(link="https://x.test", status_code=403))
    )
    assert result is not None
    assert result.status == LinkStatus.ERRO_HTTP


def test_500_returns_http_error() -> None:
    result = HttpErrorRule().match(
        ValidationContext(http_result=HttpCheckResult(link="https://x.test", status_code=500))
    )
    assert result is not None
    assert result.status == LinkStatus.ERRO_HTTP


def test_503_returns_http_error() -> None:
    result = HttpErrorRule().match(
        ValidationContext(http_result=HttpCheckResult(link="https://x.test", status_code=503))
    )
    assert result is not None
    assert result.status == LinkStatus.ERRO_HTTP


def test_200_returns_none() -> None:
    result = HttpErrorRule().match(
        ValidationContext(http_result=HttpCheckResult(link="https://x.test", status_code=200))
    )
    assert result is None


def test_302_returns_none() -> None:
    result = HttpErrorRule().match(
        ValidationContext(http_result=HttpCheckResult(link="https://x.test", status_code=302))
    )
    assert result is None


def test_no_status_code_returns_none() -> None:
    result = HttpErrorRule().match(
        ValidationContext(http_result=HttpCheckResult(link="https://x.test"))
    )
    assert result is None


def test_timed_out_returns_none() -> None:
    result = HttpErrorRule().match(
        ValidationContext(
            http_result=HttpCheckResult(link="https://x.test", timed_out=True, error="Timeout")
        )
    )
    assert result is None
