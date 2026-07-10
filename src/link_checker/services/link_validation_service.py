from __future__ import annotations

from link_checker.checkers.base import HttpCheckerProtocol
from link_checker.enums import LinkStatus
from link_checker.models import (
    InputLinkRecord,
    ValidationContext,
    ValidationResult,
)
from link_checker.rules.registry import RuleRegistry


class LinkValidationService:
    def __init__(
        self,
        *,
        http_checker: HttpCheckerProtocol,
        rule_registry: RuleRegistry,
    ) -> None:
        self.http_checker = http_checker
        self.rule_registry = rule_registry

    def validate(self, record: InputLinkRecord) -> ValidationResult:
        try:
            http_result = self.http_checker.check(record.link)
        except Exception as exc:
            return ValidationResult.from_record(
                record,
                status=LinkStatus.ERRO_TECNICO,
                technical_error=str(exc),
            )

        try:
            match = self.rule_registry.classify(ValidationContext(http_result=http_result))
        except Exception as exc:
            return ValidationResult.from_record(
                record,
                status=LinkStatus.ERRO_TECNICO,
                http_result=http_result,
                technical_error=f"Falha na classificacao: {exc}",
            )
        if match:
            return ValidationResult.from_record(
                record,
                status=match.status,
                http_result=http_result,
                rule_match=match,
            )

        return ValidationResult.from_record(
            record,
            status=LinkStatus.INDETERMINADO,
            http_result=http_result,
        )
