from link_checker.enums import LinkStatus
from link_checker.models import HttpCheckResult, InputLinkRecord
from link_checker.rules.registry import RuleRegistry
from link_checker.services.link_validation_service import LinkValidationService


class FakeChecker:
    def __init__(self, result: HttpCheckResult | Exception) -> None:
        self.result = result

    def check(self, url: str) -> HttpCheckResult:
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class ExplodingRegistry:
    def classify(self, _context):
        raise RuntimeError("rule boom")


def input_record() -> InputLinkRecord:
    return InputLinkRecord(
        participante="Ana",
        email="ana@example.com",
        empresa="ACME",
        evento_esperado="Evento",
        link="https://x.test",
    )


def test_returns_indeterminate_when_no_rule_matches() -> None:
    service = LinkValidationService(
        http_checker=FakeChecker(HttpCheckResult(link="https://x.test", status_code=200)),
        rule_registry=RuleRegistry([]),
    )

    result = service.validate(input_record())

    assert result.status == LinkStatus.INDETERMINADO


def test_returns_technical_error_when_checker_raises() -> None:
    service = LinkValidationService(
        http_checker=FakeChecker(RuntimeError("boom")),
        rule_registry=RuleRegistry([]),
    )

    result = service.validate(input_record())

    assert result.status == LinkStatus.ERRO_TECNICO
    assert "boom" in (result.technical_error or "")


def test_returns_technical_error_when_rule_raises() -> None:
    service = LinkValidationService(
        http_checker=FakeChecker(HttpCheckResult(link="https://x.test", status_code=200)),
        rule_registry=ExplodingRegistry(),
    )

    result = service.validate(input_record())

    assert result.status == LinkStatus.ERRO_TECNICO
    assert "rule boom" in (result.technical_error or "")


def test_returns_timeout_when_checker_returns_timeout() -> None:
    service = LinkValidationService(
        http_checker=FakeChecker(
            HttpCheckResult(link="https://x.test", timed_out=True, error="Timeout")
        ),
        rule_registry=RuleRegistry(),
    )

    result = service.validate(input_record())

    assert result.status == LinkStatus.TIMEOUT
    assert result.technical_error is not None


def test_returns_morto_404_when_checker_returns_404() -> None:
    service = LinkValidationService(
        http_checker=FakeChecker(HttpCheckResult(link="https://x.test", status_code=404)),
        rule_registry=RuleRegistry(),
    )

    result = service.validate(input_record())

    assert result.status == LinkStatus.MORTO_404


def test_returns_http_error_when_checker_returns_500() -> None:
    service = LinkValidationService(
        http_checker=FakeChecker(HttpCheckResult(link="https://x.test", status_code=500)),
        rule_registry=RuleRegistry(),
    )

    result = service.validate(input_record())

    assert result.status == LinkStatus.ERRO_HTTP


def test_returns_invalido_suporte_when_200_with_support_text() -> None:
    service = LinkValidationService(
        http_checker=FakeChecker(
            HttpCheckResult(
                link="https://x.test",
                status_code=200,
                response_text="Problemas com os dados de acesso. Entre em contato.",
            )
        ),
        rule_registry=RuleRegistry(),
    )

    result = service.validate(input_record())

    assert result.status == LinkStatus.INVALIDO_SUPORTE


def test_returns_indeterminate_when_200_with_generic_text() -> None:
    service = LinkValidationService(
        http_checker=FakeChecker(
            HttpCheckResult(
                link="https://x.test",
                status_code=200,
                response_text="Pagina generica sem sinais de problema ou cadastro.",
            )
        ),
        rule_registry=RuleRegistry(),
    )

    result = service.validate(input_record())

    assert result.status == LinkStatus.INDETERMINADO


def test_returns_ok_when_200_with_inscricao_url() -> None:
    service = LinkValidationService(
        http_checker=FakeChecker(
            HttpCheckResult(
                link="https://x.test",
                status_code=200,
                final_url="https://test.com/hotsite/inscricoes-participantes/form/123",
            )
        ),
        rule_registry=RuleRegistry(),
    )

    result = service.validate(input_record())

    assert result.status == LinkStatus.OK


def test_returns_ok_when_inscricao_url_has_entre_em_contato_text() -> None:
    service = LinkValidationService(
        http_checker=FakeChecker(
            HttpCheckResult(
                link="https://x.test",
                status_code=200,
                final_url="https://test.com/hotsite/inscricoes-participantes/form/123",
                response_text="Entre em contato",
            )
        ),
        rule_registry=RuleRegistry(),
    )

    result = service.validate(input_record())

    assert result.status == LinkStatus.OK


def test_returns_ok_when_inscricao_url_has_suporte_text() -> None:
    service = LinkValidationService(
        http_checker=FakeChecker(
            HttpCheckResult(
                link="https://x.test",
                status_code=200,
                final_url="https://test.com/hotsite/inscricoes-participantes/form/123",
                response_text="suporte",
            )
        ),
        rule_registry=RuleRegistry(),
    )

    result = service.validate(input_record())

    assert result.status == LinkStatus.OK


def test_returns_ok_when_inscricao_url_has_erro_text() -> None:
    service = LinkValidationService(
        http_checker=FakeChecker(
            HttpCheckResult(
                link="https://x.test",
                status_code=200,
                final_url="https://test.com/hotsite/inscricoes-participantes/form/123",
                response_text="erro",
            )
        ),
        rule_registry=RuleRegistry(),
    )

    result = service.validate(input_record())

    assert result.status == LinkStatus.OK


def test_returns_invalido_suporte_when_200_with_controladora_erro_url() -> None:
    service = LinkValidationService(
        http_checker=FakeChecker(
            HttpCheckResult(
                link="https://x.test",
                status_code=200,
                final_url="https://test.com/hotsite/controladora/erro/cio/123",
            )
        ),
        rule_registry=RuleRegistry(),
    )

    result = service.validate(input_record())

    assert result.status == LinkStatus.INVALIDO_SUPORTE


def test_returns_ok_when_200_with_inscricao_url_no_hotsite() -> None:
    service = LinkValidationService(
        http_checker=FakeChecker(
            HttpCheckResult(
                link="https://x.test",
                status_code=200,
                final_url=(
                    "https://example.com/inscricoes-participantes/form/"
                    "codigoevento/1117/lang/pt_br/redir/teste"
                ),
            )
        ),
        rule_registry=RuleRegistry(),
    )

    result = service.validate(input_record())

    assert result.status == LinkStatus.OK


def test_returns_ok_when_200_with_inscricao_text() -> None:
    service = LinkValidationService(
        http_checker=FakeChecker(
            HttpCheckResult(
                link="https://x.test",
                status_code=200,
                response_text="Sua inscricao foi confirmada, participante!",
            )
        ),
        rule_registry=RuleRegistry(),
    )

    result = service.validate(input_record())

    assert result.status == LinkStatus.OK


def test_returns_invalido_suporte_when_text_has_participante_but_support_error() -> None:
    service = LinkValidationService(
        http_checker=FakeChecker(
            HttpCheckResult(
                link="https://x.test",
                status_code=200,
                response_text="Problemas com os dados de acesso, participante.",
            )
        ),
        rule_registry=RuleRegistry(),
    )

    result = service.validate(input_record())

    assert result.status == LinkStatus.INVALIDO_SUPORTE


def test_returns_timeout_when_timeout_with_inscricao_text() -> None:
    service = LinkValidationService(
        http_checker=FakeChecker(
            HttpCheckResult(
                link="https://x.test",
                timed_out=True,
                error="Timeout",
                response_text="Sua inscricao foi confirmada.",
            )
        ),
        rule_registry=RuleRegistry(),
    )

    result = service.validate(input_record())

    assert result.status == LinkStatus.TIMEOUT


def test_returns_technical_error_when_error_with_inscricao_text() -> None:
    service = LinkValidationService(
        http_checker=FakeChecker(
            HttpCheckResult(
                link="https://x.test",
                timed_out=False,
                error="Connection refused",
                response_text="Sua inscricao foi confirmada.",
            )
        ),
        rule_registry=RuleRegistry(),
    )

    result = service.validate(input_record())

    assert result.status == LinkStatus.ERRO_TECNICO


def test_returns_morto_404_when_404_with_inscricao_text() -> None:
    service = LinkValidationService(
        http_checker=FakeChecker(
            HttpCheckResult(
                link="https://x.test",
                status_code=404,
                response_text="Sua inscricao nao foi encontrada.",
            )
        ),
        rule_registry=RuleRegistry(),
    )

    result = service.validate(input_record())

    assert result.status == LinkStatus.MORTO_404


def test_returns_http_error_when_500_with_inscricao_text() -> None:
    service = LinkValidationService(
        http_checker=FakeChecker(
            HttpCheckResult(
                link="https://x.test",
                status_code=500,
                response_text="Erro interno ao processar inscricao.",
            )
        ),
        rule_registry=RuleRegistry(),
    )

    result = service.validate(input_record())

    assert result.status == LinkStatus.ERRO_HTTP


def test_returns_indeterminate_when_200_with_generic_text_without_signals() -> None:
    service = LinkValidationService(
        http_checker=FakeChecker(
            HttpCheckResult(
                link="https://x.test",
                status_code=200,
                response_text="Pagina generica sem sinais de cadastro.",
            )
        ),
        rule_registry=RuleRegistry(),
    )

    result = service.validate(input_record())

    assert result.status == LinkStatus.INDETERMINADO


def test_returns_technical_error_when_technical_error_not_timeout() -> None:
    service = LinkValidationService(
        http_checker=FakeChecker(
            HttpCheckResult(
                link="https://x.test",
                timed_out=False,
                error="Name resolution failed",
            )
        ),
        rule_registry=RuleRegistry(),
    )

    result = service.validate(input_record())

    assert result.status == LinkStatus.ERRO_TECNICO
    assert "Name resolution failed" in (result.technical_error or "")
