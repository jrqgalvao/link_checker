from __future__ import annotations

from unittest import mock

import pytest

from link_checker import cli


def test_cli_returns_error_message_for_read_failure(capsys: pytest.CaptureFixture[str]) -> None:
    with (
        mock.patch("sys.argv", ["link-checker", "--dry-run", "--input", "missing.xlsx"]),
        mock.patch.object(cli.InputReader, "read", side_effect=ValueError("Planilha Excel vazia.")),
    ):
        with pytest.raises(SystemExit) as exc_info:
            cli.main()

    assert exc_info.value.code == 1
    assert "Erro: Planilha Excel vazia." in capsys.readouterr().err


def test_cli_passes_technical_report_path() -> None:
    with (
        mock.patch(
            "sys.argv",
            [
                "link-checker",
                "--input",
                "input.xlsx",
                "--output",
                "report.xlsx",
                "--technical-report",
                "technical.csv",
            ],
        ),
        mock.patch.object(cli, "run", return_value={}) as run_mock,
    ):
        cli.main()

    assert run_mock.call_args.args[0].name == "input.xlsx"
    assert run_mock.call_args.args[1].name == "report.xlsx"
    assert run_mock.call_args.kwargs["technical_output_path"].name == "technical.csv"


def test_cli_passes_overwrite() -> None:
    with (
        mock.patch(
            "sys.argv",
            [
                "link-checker",
                "--input",
                "input.xlsx",
                "--output",
                "report.xlsx",
                "--overwrite",
            ],
        ),
        mock.patch.object(cli, "run", return_value={}) as run_mock,
    ):
        cli.main()

    assert run_mock.call_args.kwargs["overwrite"] is True
