from __future__ import annotations

import os
import threading
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from link_checker.config import Settings
from link_checker.enums import LinkStatus
from link_checker.models import ValidationResult

if TYPE_CHECKING:
    from link_checker.io.input_reader import InputReader
    from link_checker.io.report_writer import ReportWriter

ProgressCallback = Callable[[int, int], None]
Validator = Callable[[Path, ProgressCallback | None], list[ValidationResult]]


class LinkCheckerUIApi:
    def __init__(
        self,
        *,
        settings: Settings | None = None,
        input_reader: InputReader | None = None,
        report_writer: ReportWriter | None = None,
        validator: Validator | None = None,
        reports_dir: Path | None = None,
    ) -> None:
        self._settings = settings or Settings()
        self._input_reader_obj = input_reader
        self._report_writer_obj = report_writer
        self._validator = validator or self._validate_file  # type: ignore[assignment]
        self._reports_dir = reports_dir or self._settings.reports_dir
        self._window: Any | None = None
        self._selected_path: Path | None = None
        self._selected_total = 0
        self._results: list[ValidationResult] = []
        self._processed = 0
        self._lock = threading.Lock()
        self._state = "idle"
        self._error: str | None = None
        self._job_id = 0

    def set_window(self, window: Any) -> None:
        self._window = window

    def selecionar_arquivo(self) -> dict[str, object]:
        if self._window is None:
            return {"ok": False, "erro": "Janela da UI nao inicializada."}

        with self._lock:
            if self._state in {"selecting", "loading", "validating"}:
                return {"ok": False, "erro": "Aguarde a operacao atual terminar."}
            self._job_id += 1
            job_id = self._job_id
            self._selected_path = None
            self._selected_total = 0
            self._results = []
            self._state = "selecting"
            self._error = None

        threading.Thread(
            target=self._run_file_selection,
            args=(job_id,),
            daemon=True,
        ).start()
        return {"ok": True, "state": "selecting"}

    def carregar_arquivo(self, path: str) -> dict[str, object]:
        file_path = Path(path)
        try:
            records = self._input_reader().read(file_path)
        except Exception as exc:
            return {"ok": False, "erro": str(exc)}

        with self._lock:
            self._job_id += 1
            self._selected_path = file_path
            self._selected_total = len(records)
            self._results = []
            self._state = "idle"
            self._error = None
        return {
            "ok": True,
            "path": str(file_path),
            "nome": file_path.name,
            "total": len(records),
        }

    def validar(self, path: str | None = None) -> dict[str, object]:
        file_path = Path(path) if path else self._selected_path
        if file_path is None:
            return {"ok": False, "erro": "Selecione uma planilha antes de validar."}

        with self._lock:
            if self._state == "validating":
                return {"ok": False, "erro": "Validacao ja em andamento."}
            self._job_id += 1
            job_id = self._job_id
            self._selected_path = file_path
            self._results = []
            self._processed = 0
            self._state = "validating"
            self._error = None

        thread = threading.Thread(
            target=self._run_validation,
            args=(job_id, file_path),
            daemon=True,
        )
        thread.start()
        return {"ok": True, "state": "validating"}

    def get_status(self, include_rows: bool = False) -> dict[str, object]:
        with self._lock:
            state = self._state
            error = self._error
            total = self._selected_total
            results = list(self._results)

        if state == "idle":
            return {"ok": True, "state": "idle"}
        if state == "selecting":
            return {"ok": True, "state": "selecting"}
        if state == "cancelled":
            return {"ok": True, "state": "cancelled"}
        if state == "loading":
            return {"ok": True, "state": "loading"}
        if state == "loaded":
            response = {"ok": True, "state": "loaded", "total": total}
            if self._selected_path is not None:
                response["path"] = str(self._selected_path)
                response["nome"] = self._selected_path.name
            return response
        if state == "validating":
            return {"ok": True, "state": "validating", "total": total, "processed": self._processed}
        if state == "error":
            return {"ok": True, "state": "error", "erro": error or "Erro desconhecido."}

        response: dict[str, object] = {
            "ok": True,
            "state": "done",
            "total": len(results),
            "processed": len(results),
            "kpis": _build_kpis(results),
        }
        if include_rows:
            response["rows"] = [
                _result_to_row(index, result) for index, result in enumerate(results)
            ]
        return response

    def exportar(
        self,
        apenas_visiveis: bool = False,
        indices: list[int] | None = None,
        path: str | None = None,
    ) -> dict[str, object]:
        selected = self._select_results(apenas_visiveis, indices)
        if selected is None:
            return {"ok": False, "erro": "Nenhum resultado para exportar."}

        output_path = self._resolve_export_path(path, "resultado.xlsx")
        if output_path is None:
            return {"ok": False, "erro": "Exportacao cancelada."}

        try:
            self._report_writer().write(selected, output_path, overwrite=True)
        except Exception as exc:
            return {"ok": False, "erro": str(exc)}
        return {"ok": True, "path": str(output_path), "nome": output_path.name}

    def exportar_tecnico(
        self, apenas_visiveis: bool = False, indices: list[int] | None = None
    ) -> dict[str, object]:
        selected = self._select_results(apenas_visiveis, indices)
        if selected is None:
            return {"ok": False, "erro": "Nenhum resultado para exportar."}

        path = self._reports_dir / "resultado_tecnico_ui.csv"
        try:
            self._report_writer().write_technical(selected, path, overwrite=True)
        except Exception as exc:
            return {"ok": False, "erro": str(exc)}
        return {"ok": True, "path": str(path), "nome": path.name}

    def abrir_arquivo(self, path: str) -> dict[str, object]:
        try:
            os.startfile(Path(path))
        except Exception as exc:
            return {"ok": False, "erro": str(exc)}
        return {"ok": True}

    def abrir_pasta(self, path: str) -> dict[str, object]:
        try:
            folder = Path(path).parent if Path(path).suffix else Path(path)
            os.startfile(folder)
        except Exception as exc:
            return {"ok": False, "erro": str(exc)}
        return {"ok": True}

    def limpar(self) -> dict[str, object]:
        with self._lock:
            self._job_id += 1
            self._selected_path = None
            self._selected_total = 0
            self._results = []
            self._processed = 0
            self._state = "idle"
            self._error = None
        return {"ok": True}

    def _select_results(
        self, apenas_visiveis: bool, indices: list[int] | None
    ) -> list[ValidationResult] | None:
        with self._lock:
            results = list(self._results)
        if not results:
            return None
        if not apenas_visiveis:
            return results

        visible = indices or []
        selected = [results[index] for index in visible if 0 <= index < len(results)]
        return selected or None

    def _run_file_selection(self, job_id: int) -> None:
        try:
            import webview

            paths = self._window.create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=False,
                file_types=("Planilhas (*.xlsx;*.xlsm;*.xls;*.csv)",),
            )
        except Exception as exc:
            with self._lock:
                if job_id == self._job_id:
                    self._state = "error"
                    self._error = str(exc)
            return

        if not paths:
            with self._lock:
                if job_id == self._job_id:
                    self._state = "cancelled"
            return

        file_path = Path(paths[0])
        with self._lock:
            if job_id != self._job_id:
                return
            self._selected_path = file_path
            self._state = "loading"
        self._run_file_load(job_id, file_path)

    def _run_file_load(self, job_id: int, file_path: Path) -> None:
        try:
            records = self._input_reader().read(file_path)
        except Exception as exc:
            with self._lock:
                if job_id == self._job_id:
                    self._state = "error"
                    self._error = str(exc)
            return

        with self._lock:
            if job_id != self._job_id:
                return
            self._selected_total = len(records)
            self._state = "loaded"
            self._error = None

    def _run_validation(self, job_id: int, file_path: Path) -> None:
        self._processed = 0
        try:
            results = self._validator(file_path, self._progress_callback)
        except Exception as exc:
            with self._lock:
                if job_id == self._job_id:
                    self._state = "error"
                    self._error = str(exc)
            return

        with self._lock:
            if job_id != self._job_id:
                return
            self._results = results
            self._selected_total = len(results)
            self._state = "done"
            self._error = None

    def _progress_callback(self, processed: int, total: int) -> None:
        with self._lock:
            self._processed = processed

    def _input_reader(self) -> InputReader:
        if self._input_reader_obj is None:
            from link_checker.io.input_reader import InputReader

            self._input_reader_obj = InputReader()
        return self._input_reader_obj

    def _report_writer(self) -> ReportWriter:
        if self._report_writer_obj is None:
            from link_checker.io.report_writer import ReportWriter

            self._report_writer_obj = ReportWriter()
        return self._report_writer_obj

    def _validate_file(
        self, path: Path, progress_callback: ProgressCallback | None = None
    ) -> list[ValidationResult]:
        from link_checker.runner import validate_file

        return validate_file(path, self._settings, progress_callback)

    def _resolve_export_path(self, path: str | None, default_name: str) -> Path | None:
        if path:
            return _with_default_suffix(Path(path), ".xlsx")
        if self._window is None:
            return self._reports_dir / default_name

        try:
            import webview

            selected = self._window.create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename=default_name,
                file_types=("Excel (*.xlsx)",),
            )
        except Exception:
            return None

        if not selected:
            return None
        if isinstance(selected, str):
            return _with_default_suffix(Path(selected), ".xlsx")
        return _with_default_suffix(Path(selected[0]), ".xlsx")


def _build_kpis(results: list[ValidationResult]) -> dict[str, int]:
    ativos = sum(result.status == LinkStatus.OK for result in results)
    return {
        "total": len(results),
        "ativos": ativos,
        "inativos": len(results) - ativos,
    }


def _result_to_row(index: int, result: ValidationResult) -> dict[str, object]:
    return {
        "idx": index,
        "participante": result.participante,
        "empresa": result.empresa,
        "link": result.link,
        "resultado": "OK" if result.status == LinkStatus.OK else "ERRO",
        "status": result.status.value,
        "http_status": result.http_status,
        "final_url": result.final_url,
        "rule_name": result.rule_name,
        "evidence": result.evidence or result.technical_error or "",
    }


def _with_default_suffix(path: Path, suffix: str) -> Path:
    return path.with_suffix(suffix) if not path.suffix else path
