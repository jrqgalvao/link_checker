from __future__ import annotations

import unicodedata


def normalize_text(value: str) -> str:
    without_accents = "".join(
        char for char in unicodedata.normalize("NFKD", value) if not unicodedata.combining(char)
    )
    return without_accents.casefold()
