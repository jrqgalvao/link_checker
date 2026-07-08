from link_checker.enums import LinkStatus
from link_checker.models import HttpCheckResult, ValidationContext
from link_checker.rules.support_error_rule import SupportErrorRule


def _context(
    *,
    status_code: int | None = 200,
    response_text: str | None = "",
    final_url: str | None = None,
    error: str | None = None,
    timed_out: bool = False,
) -> ValidationContext:
    return ValidationContext(
        http_result=HttpCheckResult(
            link="https://x.test",
            status_code=status_code,
            final_url=final_url,
            response_text=response_text,
            error=error,
            timed_out=timed_out,
        )
    )


def test_detects_problemas_acesso() -> None:
    match = SupportErrorRule().match(
        _context(response_text="Problemas com os dados de acesso. Entre em contato.")
    )
    assert match is not None
    assert match.status == LinkStatus.INVALIDO_SUPORTE


def test_detects_final_url_controladora_erro() -> None:
    match = SupportErrorRule().match(
        _context(final_url="https://x.test/hotsite/controladora/erro/cio/123")
    )
    assert match is not None
    assert match.status == LinkStatus.INVALIDO_SUPORTE


def test_detects_dados_de_acesso_with_entre_em_contato() -> None:
    match = SupportErrorRule().match(
        _context(response_text="Dados de acesso invalidos. Entre em contato.")
    )
    assert match is not None
    assert match.status == LinkStatus.INVALIDO_SUPORTE


def test_generic_entre_em_contato_returns_none() -> None:
    match = SupportErrorRule().match(_context(response_text="Entre em contato com a equipe."))
    assert match is None


def test_generic_suporte_word_returns_none() -> None:
    match = SupportErrorRule().match(
        _context(response_text="Central de suporte disponivel no rodape da pagina.")
    )
    assert match is None


def test_generic_erro_word_returns_none() -> None:
    match = SupportErrorRule().match(
        _context(response_text="Pagina de ajuda: como corrigir erro de digitacao.")
    )
    assert match is None


def test_detects_link_invalido_com_acento() -> None:
    match = SupportErrorRule().match(
        _context(response_text="Link inv\u00e1lido. Entre em contato com o suporte.")
    )
    assert match is not None
    assert match.status == LinkStatus.INVALIDO_SUPORTE


def test_detects_link_invalido_sem_acento() -> None:
    match = SupportErrorRule().match(
        _context(response_text="Link invalido. Entre em contato com o suporte.")
    )
    assert match is not None
    assert match.status == LinkStatus.INVALIDO_SUPORTE


def test_detects_acesso_invalido_com_acento() -> None:
    match = SupportErrorRule().match(
        _context(response_text="Acesso inv\u00e1lido. Entre em contato com o suporte.")
    )
    assert match is not None
    assert match.status == LinkStatus.INVALIDO_SUPORTE


def test_detects_acesso_invalido_sem_acento() -> None:
    match = SupportErrorRule().match(
        _context(response_text="Acesso invalido. Entre em contato com o suporte.")
    )
    assert match is not None
    assert match.status == LinkStatus.INVALIDO_SUPORTE


def test_detection_is_case_insensitive() -> None:
    match = SupportErrorRule().match(_context(response_text="PROBLEMAS COM OS DADOS DE ACESSO"))
    assert match is not None
    assert match.status == LinkStatus.INVALIDO_SUPORTE


def test_generic_html_returns_none() -> None:
    match = SupportErrorRule().match(
        _context(response_text="Bem-vindo ao evento! Sua inscricao foi confirmada.")
    )
    assert match is None


def test_inscricao_fake_without_error_signals_returns_none() -> None:
    match = SupportErrorRule().match(
        _context(
            response_text=(
                "<html><body>Inscricao realizada com sucesso. Acesse o evento.</body></html>"
            )
        )
    )
    assert match is None


def test_inscricao_url_with_entre_em_contato_returns_none() -> None:
    match = SupportErrorRule().match(
        _context(
            final_url="https://x.test/hotsite/inscricoes-participantes/form/123",
            response_text="Entre em contato",
        )
    )
    assert match is None


def test_inscricao_url_with_suporte_returns_none() -> None:
    match = SupportErrorRule().match(
        _context(
            final_url="https://x.test/hotsite/inscricoes-participantes/form/123",
            response_text="suporte",
        )
    )
    assert match is None


def test_inscricao_url_with_erro_returns_none() -> None:
    match = SupportErrorRule().match(
        _context(
            final_url="https://x.test/hotsite/inscricoes-participantes/form/123",
            response_text="erro",
        )
    )
    assert match is None


def test_timeout_returns_none() -> None:
    match = SupportErrorRule().match(_context(timed_out=True, error="Timeout", status_code=None))
    assert match is None


def test_technical_error_returns_none() -> None:
    match = SupportErrorRule().match(
        _context(error="Connection refused", timed_out=False, status_code=None)
    )
    assert match is None


def test_http_404_returns_none() -> None:
    match = SupportErrorRule().match(
        _context(status_code=404, response_text="Erro 404 - Pagina nao encontrada")
    )
    assert match is None


def test_http_500_returns_none() -> None:
    match = SupportErrorRule().match(
        _context(status_code=500, response_text="Erro interno do servidor")
    )
    assert match is None


def test_no_body_returns_none() -> None:
    match = SupportErrorRule().match(_context(response_text=None))
    assert match is None
