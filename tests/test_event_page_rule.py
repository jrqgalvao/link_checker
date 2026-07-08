from link_checker.enums import LinkStatus
from link_checker.models import HttpCheckResult, ValidationContext
from link_checker.rules.event_page_rule import EventPageRule


def _context(
    *,
    link: str = "https://x.test",
    status_code: int | None = 200,
    final_url: str | None = None,
    response_text: str | None = "",
    error: str | None = None,
    timed_out: bool = False,
) -> ValidationContext:
    return ValidationContext(
        http_result=HttpCheckResult(
            link=link,
            status_code=status_code,
            final_url=final_url,
            response_text=response_text,
            error=error,
            timed_out=timed_out,
        )
    )


class TestReturnsOk:
    def test_url_with_inscricao_form_route(self) -> None:
        result = EventPageRule().match(
            _context(
                final_url=(
                    "https://example.com/hotsite/inscricoes-participantes/form/codigoevento/1117"
                )
            )
        )
        assert result is not None
        assert result.status == LinkStatus.OK

    def test_text_contains_inscricao_and_participante(self) -> None:
        result = EventPageRule().match(
            _context(response_text="Sua inscricao de participante foi confirmada.")
        )
        assert result is not None
        assert result.status == LinkStatus.OK

    def test_text_contains_only_inscricao_returns_none(self) -> None:
        result = EventPageRule().match(_context(response_text="Veja detalhes da inscricao."))
        assert result is None

    def test_text_contains_only_participante_returns_none(self) -> None:
        result = EventPageRule().match(_context(response_text="Bem-vindo, Participante!"))
        assert result is None

    def test_case_insensitive_inscricao_with_participante(self) -> None:
        result = EventPageRule().match(_context(response_text="INSCRICAO DO PARTICIPANTE"))
        assert result is not None
        assert result.status == LinkStatus.OK

    def test_url_with_inscricao_form_route_no_hotsite(self) -> None:
        result = EventPageRule().match(
            _context(
                final_url="https://example.com/inscricoes-participantes/form/codigoevento/1117"
            )
        )
        assert result is not None
        assert result.status == LinkStatus.OK

    def test_production_url_returns_ok(self) -> None:
        result = EventPageRule().match(
            _context(
                final_url=(
                    "https://example.com/inscricoes-participantes/form/codigoevento/"
                    "1117/lang/pt_br/redir/teste"
                )
            )
        )
        assert result is not None
        assert result.status == LinkStatus.OK

    def test_original_registration_url_redirected_to_login_returns_ok(self) -> None:
        result = EventPageRule().match(
            _context(
                link=(
                    "https://test.com/hotsite/inscricoes-participantes/form/"
                    "codigoevento/1117/lang/pt_br/redir/teste"
                ),
                final_url="https://test.com/hotsite/login/index/url/abc/codigoevento/1117",
            )
        )
        assert result is not None
        assert result.status == LinkStatus.OK

    def test_evidence_is_clear(self) -> None:
        result = EventPageRule().match(
            _context(final_url="https://test.com/hotsite/inscricoes-participantes/form/123")
        )
        assert result is not None
        assert "URL" in result.evidence or "inscricao" in result.evidence


class TestReturnsNone:
    def test_timeout(self) -> None:
        result = EventPageRule().match(_context(timed_out=True, error="Timeout", status_code=None))
        assert result is None

    def test_technical_error(self) -> None:
        result = EventPageRule().match(
            _context(error="Connection refused", timed_out=False, status_code=None)
        )
        assert result is None

    def test_status_code_none(self) -> None:
        result = EventPageRule().match(
            _context(status_code=None, response_text="Inscricao confirmada")
        )
        assert result is None

    def test_http_404(self) -> None:
        result = EventPageRule().match(
            _context(status_code=404, response_text="Inscricao nao encontrada")
        )
        assert result is None

    def test_http_500(self) -> None:
        result = EventPageRule().match(
            _context(status_code=500, response_text="Erro interno com inscricao")
        )
        assert result is None

    def test_http_204_no_body(self) -> None:
        result = EventPageRule().match(_context(status_code=204, response_text=None))
        assert result is None

    def test_http_302_without_registration_url(self) -> None:
        result = EventPageRule().match(
            _context(
                status_code=302,
                final_url="https://login.example.com",
                response_text="",
            )
        )
        assert result is None

    def test_generic_html(self) -> None:
        result = EventPageRule().match(_context(response_text="Bem-vindo ao portal."))
        assert result is None

    def test_only_evento_text(self) -> None:
        result = EventPageRule().match(_context(response_text="Venha para o Evento anual!"))
        assert result is None

    def test_support_text_problemas_acesso(self) -> None:
        result = EventPageRule().match(
            _context(response_text="Problemas com os dados de acesso, participante.")
        )
        assert result is None

    def test_support_text_entre_em_contato(self) -> None:
        result = EventPageRule().match(
            _context(response_text="Entre em contato com o suporte, participante.")
        )
        assert result is None

    def test_support_text_link_invalido(self) -> None:
        result = EventPageRule().match(_context(response_text="Link invalido para inscricao."))
        assert result is None

    def test_support_text_suporte(self) -> None:
        result = EventPageRule().match(_context(response_text="Suporte ao participante."))
        assert result is None

    def test_controladora_erro_url_returns_none(self) -> None:
        result = EventPageRule().match(
            _context(final_url="https://test.com/hotsite/controladora/erro/cio/123")
        )
        assert result is None

    def test_original_registration_url_with_final_error_returns_none(self) -> None:
        result = EventPageRule().match(
            _context(
                link="https://test.com/hotsite/inscricoes-participantes/form/123",
                final_url="https://test.com/hotsite/controladora/erro/cio/123",
            )
        )
        assert result is None

    def test_generic_domain_returns_none(self) -> None:
        result = EventPageRule().match(_context(final_url="https://example.com/"))
        assert result is None

    def test_http_302_with_registration_url(self) -> None:
        result = EventPageRule().match(
            _context(
                status_code=302,
                final_url="https://test.com/hotsite/inscricoes-participantes/form/abc",
                response_text="",
            )
        )
        assert result is not None
        assert result.status == LinkStatus.OK
