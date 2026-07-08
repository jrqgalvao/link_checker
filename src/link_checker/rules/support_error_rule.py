from __future__ import annotations

from link_checker.enums import LinkStatus
from link_checker.models import RuleMatch, ValidationContext
from link_checker.utils.text import normalize_text


class SupportErrorRule:
    name = "support_error"
    error_url_terms = ("/controladora/erro/",)
    strong_text_terms = (
        "problemas com os dados de acesso",
        "link invalido",
        "acesso invalido",
    )
    combined_text_terms = (("dados de acesso", "entre em contato"),)

    def match(self, context: ValidationContext) -> RuleMatch | None:
        http = context.http_result

        if http.timed_out:
            return None

        if http.error:
            return None

        if http.status_code is not None and http.status_code >= 400:
            return None

        normalized_url = normalize_text(http.final_url or "")
        for phrase in self.error_url_terms:
            if normalize_text(phrase) in normalized_url:
                return self._match(phrase)

        normalized_text = normalize_text(context.text)
        for phrase in self.strong_text_terms:
            if normalize_text(phrase) in normalized_text:
                return self._match(phrase)

        for terms in self.combined_text_terms:
            normalized_terms = tuple(normalize_text(term) for term in terms)
            if all(term in normalized_text for term in normalized_terms):
                return self._match(" + ".join(terms))
        return None

    def _match(self, evidence: str) -> RuleMatch:
        return RuleMatch(
            LinkStatus.INVALIDO_SUPORTE,
            self.name,
            f"Pagina de erro/suporte detectada: {evidence}",
        )
