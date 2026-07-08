from __future__ import annotations

from pathlib import Path
from unittest import mock

from link_checker.config import Settings
from link_checker.enums import LinkStatus
from link_checker.models import InputLinkRecord, ValidationResult
from link_checker.runner import run


def test_runner_orchestrates_reader_service_writer(tmp_path: Path) -> None:
    record = InputLinkRecord("", "", "ACME", "", "https://x.test")
    result = ValidationResult.from_record(record, status=LinkStatus.OK)
    output = tmp_path / "report.xlsx"

    with (
        mock.patch("link_checker.runner.InputReader") as reader_cls,
        mock.patch("link_checker.runner.LinkValidationService") as service_cls,
        mock.patch("link_checker.runner.ReportWriter") as writer_cls,
    ):
        reader_cls.return_value.read.return_value = [record]
        service_cls.return_value.validate.return_value = result

        summary = run(tmp_path / "input.xlsx", output)

    assert summary == {LinkStatus.OK: 1}
    reader_cls.return_value.read.assert_called_once_with(tmp_path / "input.xlsx")
    service_cls.return_value.validate.assert_called_once_with(record)
    writer_cls.return_value.write.assert_called_once_with([result], output, overwrite=False)


def test_runner_writes_optional_technical_report(tmp_path: Path) -> None:
    record = InputLinkRecord("", "", "ACME", "", "https://x.test")
    result = ValidationResult.from_record(record, status=LinkStatus.OK)
    output = tmp_path / "report.xlsx"
    technical_output = tmp_path / "technical.csv"

    with (
        mock.patch("link_checker.runner.InputReader") as reader_cls,
        mock.patch("link_checker.runner.LinkValidationService") as service_cls,
        mock.patch("link_checker.runner.ReportWriter") as writer_cls,
    ):
        reader_cls.return_value.read.return_value = [record]
        service_cls.return_value.validate.return_value = result

        run(tmp_path / "input.xlsx", output, technical_output_path=technical_output)

    writer_cls.return_value.write.assert_called_once_with([result], output, overwrite=False)
    writer_cls.return_value.write_technical.assert_called_once_with(
        [result], technical_output, overwrite=False
    )


def test_runner_passes_overwrite_to_writers(tmp_path: Path) -> None:
    record = InputLinkRecord("", "", "ACME", "", "https://x.test")
    result = ValidationResult.from_record(record, status=LinkStatus.OK)
    output = tmp_path / "report.xlsx"
    technical_output = tmp_path / "technical.csv"

    with (
        mock.patch("link_checker.runner.InputReader") as reader_cls,
        mock.patch("link_checker.runner.LinkValidationService") as service_cls,
        mock.patch("link_checker.runner.ReportWriter") as writer_cls,
    ):
        reader_cls.return_value.read.return_value = [record]
        service_cls.return_value.validate.return_value = result

        run(
            tmp_path / "input.xlsx",
            output,
            technical_output_path=technical_output,
            overwrite=True,
        )

    writer_cls.return_value.write.assert_called_once_with([result], output, overwrite=True)
    writer_cls.return_value.write_technical.assert_called_once_with(
        [result], technical_output, overwrite=True
    )


def test_runner_uses_parallel_workers_and_preserves_order(tmp_path: Path) -> None:
    records = [
        InputLinkRecord("A", "", "ACME", "", "https://x.test/a"),
        InputLinkRecord("B", "", "ACME", "", "https://x.test/b"),
    ]
    results = [
        ValidationResult.from_record(records[0], status=LinkStatus.OK),
        ValidationResult.from_record(records[1], status=LinkStatus.ERRO_HTTP),
    ]
    output = tmp_path / "report.xlsx"
    settings = Settings(max_workers=2)

    future1 = mock.MagicMock()
    future1.result.return_value = results[0]
    future2 = mock.MagicMock()
    future2.result.return_value = results[1]

    with (
        mock.patch("link_checker.runner.InputReader") as reader_cls,
        mock.patch("link_checker.runner.LinkValidationService"),
        mock.patch("link_checker.runner.ReportWriter") as writer_cls,
        mock.patch("link_checker.runner.ThreadPoolExecutor") as executor_cls,
        mock.patch("link_checker.runner.as_completed") as as_completed_mock,
    ):
        executor_instance = mock.MagicMock()
        executor_cls.return_value.__enter__.return_value = executor_instance
        executor_instance.submit.side_effect = [future1, future2]
        as_completed_mock.return_value = [future1, future2]
        reader_cls.return_value.read.return_value = records

        run(tmp_path / "input.xlsx", output, settings=settings)

    executor_cls.assert_called_once_with(max_workers=2)
    writer_cls.return_value.write.assert_called_once_with(results, output, overwrite=False)
