from link_checker.enums import LinkStatus
from link_checker.models import InputLinkRecord, ValidationResult


def test_validation_result_keeps_input_fields() -> None:
    record = InputLinkRecord(
        participante="Ana",
        email="ana@example.com",
        empresa="ACME",
        evento_esperado="Evento",
        link="https://x.test",
    )

    result = ValidationResult.from_record(record, status=LinkStatus.INDETERMINADO)

    assert result.participante == "Ana"
    assert result.status == LinkStatus.INDETERMINADO
