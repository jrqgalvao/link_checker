from __future__ import annotations

import sys
import threading
from pathlib import Path
from types import SimpleNamespace

from link_checker.enums import LinkStatus
from link_checker.models import InputLinkRecord, ValidationResult
from link_checker.ui.api import LinkCheckerUIApi


class FakeReader:
    def __init__(self, records: list[InputLinkRecord] | None = None) -> None:
        self.records = records or []

    def read(self, path: Path) -> list[InputLinkRecord]:
        if path.suffix == ".bad":
            raise ValueError("arquivo invalido")
        return self.records


class FakeWriter:
    def __init__(self) -> None:
        self.operational_calls: list[tuple[list[ValidationResult], Path, bool]] = []
        self.technical_calls: list[tuple[list[ValidationResult], Path, bool]] = []

    def write(
        self, results: list[ValidationResult], path: Path, *, overwrite: bool = False
    ) -> None:
        self.operational_calls.append((results, path, overwrite))

    def write_technical(
        self, results: list[ValidationResult], path: Path, *, overwrite: bool = False
    ) -> None:
        self.technical_calls.append((results, path, overwrite))


def make_result(
    participante: str,
    status: LinkStatus,
    *,
    evidence: str | None = None,
) -> ValidationResult:
    record = InputLinkRecord(
        participante=participante,
        email="",
        empresa="ACME",
        evento_esperado="",
        link=f"https://example.test/{participante.lower()}",
    )
    return ValidationResult.from_record(record, status=status, technical_error=evidence)


def test_validar_starts_background_job_without_returning_rows(tmp_path: Path) -> None:
    started = threading.Event()
    release = threading.Event()
    results = [
        make_result("Ana", LinkStatus.OK),
        make_result("Bia", LinkStatus.MORTO_404, evidence="404"),
    ]

    def validator(_path: Path, _progress=None) -> list[ValidationResult]:
        started.set()
        release.wait(timeout=2)
        return results

    api = LinkCheckerUIApi(validator=validator, reports_dir=tmp_path)

    response = api.validar(str(tmp_path / "entrada.xlsx"))

    assert response == {"ok": True, "state": "validating"}
    assert started.wait(timeout=1)
    status = api.get_status()
    assert status["state"] == "validating"
    assert "rows" not in status

    release.set()
    _wait_until_done(api)
    done = api.get_status(include_rows=True)
    assert done["state"] == "done"
    assert done["kpis"] == {
        "total": 2,
        "ativos": 1,
        "inativos": 1,
    }
    assert done["rows"][0]["participante"] == "Ana"
    assert done["rows"][1]["resultado"] == "ERRO"
    assert done["rows"][1]["status"] == "MORTO_404"


def test_rejects_second_validation_while_running(tmp_path: Path) -> None:
    started = threading.Event()
    release = threading.Event()

    def validator(_path: Path, _progress=None) -> list[ValidationResult]:
        started.set()
        release.wait(timeout=2)
        return [make_result("Ana", LinkStatus.OK)]

    api = LinkCheckerUIApi(validator=validator, reports_dir=tmp_path)

    first = api.validar(str(tmp_path / "entrada.xlsx"))
    assert first["ok"] is True
    assert started.wait(timeout=1)

    second = api.validar(str(tmp_path / "entrada.xlsx"))

    release.set()
    _wait_until_done(api)
    assert second == {"ok": False, "erro": "Validacao ja em andamento."}


def test_worker_error_sets_error_state(tmp_path: Path) -> None:
    def fail(_path: Path, _progress=None) -> list[ValidationResult]:
        raise ValueError("arquivo invalido")

    api = LinkCheckerUIApi(validator=fail, reports_dir=tmp_path)

    response = api.validar(str(tmp_path / "entrada.bad"))

    assert response["ok"] is True
    status = _wait_until_done(api)
    assert status == {"ok": True, "state": "error", "erro": "arquivo invalido"}


def test_upload_dry_run_returns_file_name_and_row_count(tmp_path: Path) -> None:
    records = [InputLinkRecord("Ana", "", "ACME", "", "https://example.test")]
    api = LinkCheckerUIApi(input_reader=FakeReader(records), reports_dir=tmp_path)

    response = api.carregar_arquivo(str(tmp_path / "entrada.xlsx"))

    assert response == {
        "ok": True,
        "path": str(tmp_path / "entrada.xlsx"),
        "nome": "entrada.xlsx",
        "total": 1,
    }


def test_selecionar_arquivo_starts_background_load(monkeypatch, tmp_path: Path) -> None:
    started = threading.Event()
    release = threading.Event()
    dialog_opened = threading.Event()
    release_dialog = threading.Event()
    records = [InputLinkRecord("Ana", "", "ACME", "", "https://example.test")]

    class SlowReader:
        def read(self, _path: Path) -> list[InputLinkRecord]:
            started.set()
            release.wait(timeout=2)
            return records

    class FakeWindow:
        def create_file_dialog(self, *_args, **_kwargs):
            dialog_opened.set()
            release_dialog.wait(timeout=2)
            return [str(tmp_path / "entrada.xlsx")]

    monkeypatch.setitem(sys.modules, "webview", SimpleNamespace(OPEN_DIALOG=1))
    api = LinkCheckerUIApi(input_reader=SlowReader(), reports_dir=tmp_path)
    api.set_window(FakeWindow())

    response = api.selecionar_arquivo()

    assert response == {"ok": True, "state": "selecting"}
    assert dialog_opened.wait(timeout=1)
    assert api.get_status()["state"] == "selecting"

    release_dialog.set()
    assert started.wait(timeout=1)
    assert api.get_status()["state"] == "loading"

    release.set()
    status = _wait_until_done(api)
    assert status["state"] == "loaded"
    assert status["total"] == 1


def test_exportar_operacional_uses_all_results_by_default(tmp_path: Path) -> None:
    writer = FakeWriter()
    results = [make_result("Ana", LinkStatus.OK), make_result("Bia", LinkStatus.TIMEOUT)]
    api = LinkCheckerUIApi(
        validator=lambda _path, _progress=None: results,
        report_writer=writer,
        reports_dir=tmp_path,
    )
    api.validar(str(tmp_path / "entrada.xlsx"))
    _wait_until_done(api)

    output = tmp_path / "saida.xlsx"

    response = api.exportar(False, [], str(output))

    assert response["ok"] is True
    exported, path, overwrite = writer.operational_calls[0]
    assert exported == results
    assert path == output
    assert overwrite is True


def test_exportar_operacional_uses_visible_indices(tmp_path: Path) -> None:
    writer = FakeWriter()
    results = [make_result("Ana", LinkStatus.OK), make_result("Bia", LinkStatus.TIMEOUT)]
    api = LinkCheckerUIApi(
        validator=lambda _path, _progress=None: results,
        report_writer=writer,
        reports_dir=tmp_path,
    )
    api.validar(str(tmp_path / "entrada.xlsx"))
    _wait_until_done(api)
    output = tmp_path / "visiveis.xlsx"

    response = api.exportar(True, [1], str(output))

    assert response["ok"] is True
    exported, path, overwrite = writer.operational_calls[0]
    assert exported == [results[1]]
    assert path == output
    assert overwrite is True


def test_exportar_visible_without_rows_returns_clear_error(tmp_path: Path) -> None:
    writer = FakeWriter()
    results = [make_result("Ana", LinkStatus.OK)]
    api = LinkCheckerUIApi(
        validator=lambda _path, _progress=None: results,
        report_writer=writer,
        reports_dir=tmp_path,
    )
    api.validar(str(tmp_path / "entrada.xlsx"))
    _wait_until_done(api)

    response = api.exportar(True, [], str(tmp_path / "vazio.xlsx"))

    assert response == {"ok": False, "erro": "Nenhum resultado para exportar."}
    assert writer.operational_calls == []


def test_exportar_without_results_returns_clear_error(tmp_path: Path) -> None:
    api = LinkCheckerUIApi(reports_dir=tmp_path)

    response = api.exportar(False, [], str(tmp_path / "saida.xlsx"))

    assert response == {"ok": False, "erro": "Nenhum resultado para exportar."}


def test_limpar_resets_state(tmp_path: Path) -> None:
    api = LinkCheckerUIApi(
        validator=lambda _path: [make_result("Ana", LinkStatus.OK)],
        reports_dir=tmp_path,
    )
    api.validar(str(tmp_path / "entrada.xlsx"))
    _wait_until_done(api)

    response = api.limpar()

    assert response == {"ok": True}
    assert api.get_status() == {"ok": True, "state": "idle"}


def _wait_until_done(api: LinkCheckerUIApi) -> dict[str, object]:
    for _ in range(50):
        status = api.get_status()
        if status["state"] in {"loaded", "done", "error"}:
            return status
        threading.Event().wait(0.02)
    raise AssertionError("job did not finish")
