from __future__ import annotations

from dataclasses import asdict, dataclass

from link_checker.enums import LinkStatus


@dataclass(frozen=True)
class InputLinkRecord:
    participante: str
    email: str
    empresa: str
    evento_esperado: str
    link: str


@dataclass(frozen=True)
class HttpCheckResult:
    link: str
    status_code: int | None = None
    final_url: str | None = None
    redirect_history: tuple[str, ...] = ()
    response_time_seconds: float | None = None
    response_text: str | None = None
    error: str | None = None
    timed_out: bool = False


@dataclass(frozen=True)
class RuleMatch:
    status: LinkStatus
    rule_name: str
    evidence: str


@dataclass(frozen=True)
class ValidationContext:
    http_result: HttpCheckResult

    @property
    def text(self) -> str:
        return self.http_result.response_text or ""


@dataclass(frozen=True)
class ValidationResult:
    participante: str
    email: str
    empresa: str
    evento_esperado: str
    link: str
    status: LinkStatus
    http_status: int | None = None
    final_url: str | None = None
    response_time_seconds: float | None = None
    rule_name: str | None = None
    evidence: str | None = None
    technical_error: str | None = None

    @classmethod
    def from_record(
        cls,
        record: InputLinkRecord,
        *,
        status: LinkStatus,
        http_result: HttpCheckResult | None = None,
        rule_match: RuleMatch | None = None,
        technical_error: str | None = None,
    ) -> ValidationResult:
        return cls(
            participante=record.participante,
            email=record.email,
            empresa=record.empresa,
            evento_esperado=record.evento_esperado,
            link=record.link,
            status=status,
            http_status=http_result.status_code if http_result else None,
            final_url=http_result.final_url if http_result else None,
            response_time_seconds=http_result.response_time_seconds if http_result else None,
            rule_name=rule_match.rule_name if rule_match else None,
            evidence=rule_match.evidence if rule_match else None,
            technical_error=technical_error or (http_result.error if http_result else None),
        )

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["status"] = self.status.value
        return data
