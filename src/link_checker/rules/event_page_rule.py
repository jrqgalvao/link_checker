from __future__ import annotations

import base64
from urllib.parse import unquote, urlparse

from link_checker.enums import LinkStatus
from link_checker.models import RuleMatch, ValidationContext
from link_checker.utils.text import normalize_text


class EventPageRule:
    name = "event_page"
    registration_url_patterns = (
        "/hotsite/inscricoes-participantes/form/",
        "/inscricoes-participantes/form/",
    )
    negative_url_patterns = ("/controladora/erro/",)
    required_text_signals = ("inscricao", "participante")
    negative_signals = (
        "problemas com os dados de acesso",
        "entre em contato",
        "link inválido",
        "link invalido",
        "acesso inválido",
        "acesso invalido",
        "suporte",
    )

    def match(self, context: ValidationContext) -> RuleMatch | None:
        http = context.http_result

        if http.timed_out:
            return None

        if http.error:
            return None

        if http.status_code is None:
            return None

        if http.status_code >= 400:
            return None

        normalized_url = normalize_text(http.final_url or "")
        normalized_original_url = normalize_text(http.link)
        normalized_login_target = normalize_text(_encoded_login_target(http.final_url or ""))

        for pattern in self.negative_url_patterns:
            if pattern in normalized_url:
                return None

        for pattern in self.registration_url_patterns:
            if pattern in normalized_url:
                return RuleMatch(
                    LinkStatus.OK,
                    self.name,
                    "URL final de inscricao detectada",
                )

        for pattern in self.registration_url_patterns:
            if pattern in normalized_login_target:
                return RuleMatch(
                    LinkStatus.OK,
                    self.name,
                    "URL de inscricao codificada no login detectada",
                )

        for pattern in self.registration_url_patterns:
            if pattern in normalized_original_url:
                return RuleMatch(
                    LinkStatus.OK,
                    self.name,
                    "URL original de inscricao detectada",
                )

        normalized_text = normalize_text(context.text)

        if not normalized_text:
            return None

        for signal in self.negative_signals:
            if normalize_text(signal) in normalized_text:
                return None

        if all(normalize_text(signal) in normalized_text for signal in self.required_text_signals):
            return RuleMatch(
                LinkStatus.OK,
                self.name,
                "Texto de inscricao e participante detectado",
            )

        return None


def _encoded_login_target(url: str) -> str:
    parts = urlparse(url).path.split("/")
    if "url" not in parts:
        return ""
    index = parts.index("url") + 1
    if index >= len(parts):
        return ""
    token = unquote(parts[index])
    try:
        padding = "=" * (-len(token) % 4)
        return base64.urlsafe_b64decode(token + padding).decode("utf-8", errors="replace")
    except ValueError:
        return ""
