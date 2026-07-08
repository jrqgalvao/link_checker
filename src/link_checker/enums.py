from __future__ import annotations

from enum import StrEnum


class LinkStatus(StrEnum):
    OK = "OK"
    INVALIDO_SUPORTE = "INVALIDO_SUPORTE"
    MORTO_404 = "MORTO_404"
    ERRO_HTTP = "ERRO_HTTP"
    TIMEOUT = "TIMEOUT"
    INDETERMINADO = "INDETERMINADO"
    ERRO_TECNICO = "ERRO_TECNICO"
