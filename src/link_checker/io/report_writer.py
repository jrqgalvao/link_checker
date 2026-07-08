from __future__ import annotations

import csv
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from link_checker.enums import LinkStatus
from link_checker.models import ValidationResult

_SUPPORTED_OUTPUT_EXTENSIONS = {".xlsx", ".csv"}
_OUTPUT_COLUMNS = (
    "NOME DO PARTICIPANTE",
    "NOME DA EMPRESA",
    "LINK",
    "RESULTADO",
)
_DETAILS_COLUMNS = (
    "NOME DO PARTICIPANTE",
    "NOME DA EMPRESA",
    "LINK",
    "RESULTADO",
    "STATUS_INTERNO",
    "REGRA",
    "EVIDENCIA",
    "STATUS_HTTP",
    "URL_FINAL",
    "TEMPO_RESPOSTA_MS",
    "ERRO_TECNICO",
)
_TECHNICAL_COLUMNS = (
    "participante",
    "empresa",
    "link",
    "status",
    "http_status",
    "final_url",
    "response_time_seconds",
    "rule_name",
    "evidence",
    "technical_error",
)


class ReportWriter:
    def write(
        self, results: list[ValidationResult], path: Path, *, overwrite: bool = False
    ) -> None:
        suffix = path.suffix.lower()
        if suffix not in _SUPPORTED_OUTPUT_EXTENSIONS:
            raise ValueError(f"Extensao nao suportada: {suffix}. Use .csv ou .xlsx.")

        _ensure_can_write(path, overwrite)
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = [self._row(r) for r in results]

        if suffix == ".csv":
            _write_csv(path, _OUTPUT_COLUMNS, rows)
        else:
            details_rows = [_details_row(result) for result in results]
            _write_xlsx(
                path,
                [
                    _Sheet("resultado", _OUTPUT_COLUMNS, rows, result_sheet=True),
                    _Sheet("detalhes", _DETAILS_COLUMNS, details_rows),
                ],
            )

    def write_technical(
        self, results: list[ValidationResult], path: Path, *, overwrite: bool = False
    ) -> None:
        suffix = path.suffix.lower()
        if suffix not in _SUPPORTED_OUTPUT_EXTENSIONS:
            raise ValueError(f"Extensao nao suportada: {suffix}. Use .csv ou .xlsx.")

        _ensure_can_write(path, overwrite)
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = [self._technical_row(r) for r in results]

        if suffix == ".csv":
            _write_csv(path, _TECHNICAL_COLUMNS, rows)
        else:
            _write_xlsx(path, [_Sheet("resultado_tecnico", _TECHNICAL_COLUMNS, rows)])

    @staticmethod
    def _row(result: ValidationResult) -> list[object]:
        return [
            result.participante,
            result.empresa,
            result.link,
            "OK" if result.status == LinkStatus.OK else "ERRO",
        ]

    @staticmethod
    def _technical_row(result: ValidationResult) -> list[object]:
        return [
            result.participante,
            result.empresa,
            result.link,
            result.status.value,
            result.http_status,
            result.final_url,
            result.response_time_seconds,
            result.rule_name,
            result.evidence,
            result.technical_error,
        ]


class _Sheet:
    def __init__(
        self,
        name: str,
        columns: tuple[str, ...],
        rows: list[list[object]],
        *,
        result_sheet: bool = False,
    ) -> None:
        self.name = name
        self.columns = columns
        self.rows = rows
        self.result_sheet = result_sheet


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[list[object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        writer.writerows(rows)


def _write_xlsx(path: Path, sheets: list[_Sheet]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _content_types(len(sheets)))
        archive.writestr("_rels/.rels", _root_rels())
        archive.writestr("xl/workbook.xml", _workbook_xml(sheets))
        archive.writestr("xl/_rels/workbook.xml.rels", _workbook_rels(len(sheets)))
        archive.writestr("xl/styles.xml", _styles_xml())
        for index, sheet in enumerate(sheets, 1):
            archive.writestr(f"xl/worksheets/sheet{index}.xml", _sheet_xml(sheet))


def _content_types(sheet_count: int) -> str:
    sheet_overrides = "".join(
        f'<Override PartName="/xl/worksheets/sheet{i}.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for i in range(1, sheet_count + 1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" '
        'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/styles.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        f"{sheet_overrides}</Types>"
    )


def _root_rels() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/></Relationships>'
    )


def _workbook_xml(sheets: list[_Sheet]) -> str:
    items = "".join(
        f'<sheet name="{escape(sheet.name)}" sheetId="{index}" r:id="rId{index}"/>'
        for index, sheet in enumerate(sheets, 1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"<sheets>{items}</sheets></workbook>"
    )


def _workbook_rels(sheet_count: int) -> str:
    sheet_rels = "".join(
        f'<Relationship Id="rId{i}" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        f'Target="worksheets/sheet{i}.xml"/>'
        for i in range(1, sheet_count + 1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f"{sheet_rels}"
        f'<Relationship Id="rId{sheet_count + 1}" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
        'Target="styles.xml"/></Relationships>'
    )


def _sheet_xml(sheet: _Sheet) -> str:
    rows = [_row_xml(1, sheet.columns, header=True, result_sheet=sheet.result_sheet)]
    rows.extend(
        _row_xml(index, row, result_sheet=sheet.result_sheet)
        for index, row in enumerate(sheet.rows, 2)
    )
    widths = _cols_xml(sheet)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"{widths}"
        '<sheetViews><sheetView workbookViewId="0">'
        '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
        "</sheetView></sheetViews>"
        f"<sheetData>{''.join(rows)}</sheetData></worksheet>"
    )


def _row_xml(
    row_number: int,
    values: tuple[str, ...] | list[object],
    *,
    header: bool = False,
    result_sheet: bool = False,
) -> str:
    cells = []
    for col_index, value in enumerate(values, 1):
        style = 1 if header else 0
        if result_sheet and row_number > 1 and col_index == 4:
            style = 2 if value == "OK" else 3
        cells.append(_cell_xml(row_number, col_index, value, style))
    return f'<row r="{row_number}">{"".join(cells)}</row>'


def _cell_xml(row_number: int, col_index: int, value: object, style: int) -> str:
    ref = f"{_column_name(col_index)}{row_number}"
    text = "" if value is None else str(value)
    return f'<c r="{ref}" s="{style}" t="inlineStr"><is><t>{escape(text)}</t></is></c>'


def _column_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def _cols_xml(sheet: _Sheet) -> str:
    widths = (
        [28, 24, 50, 12] if sheet.result_sheet else [28, 24, 42, 10, 18, 16, 28, 12, 36, 14, 28]
    )
    cols = "".join(
        f'<col min="{idx}" max="{idx}" width="{width}" customWidth="1"/>'
        for idx, width in enumerate(widths[: len(sheet.columns)], 1)
    )
    return f"<cols>{cols}</cols>"


def _styles_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="4">'
        '<font><sz val="11"/><color theme="1"/><name val="Calibri"/></font>'
        '<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font>'
        '<font><sz val="11"/><color rgb="FF006100"/><name val="Calibri"/></font>'
        '<font><sz val="11"/><color rgb="FF9C0006"/><name val="Calibri"/></font>'
        "</fonts>"
        '<fills count="5">'
        '<fill><patternFill patternType="none"/></fill>'
        '<fill><patternFill patternType="gray125"/></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FF1F4E78"/>'
        '<bgColor indexed="64"/></patternFill></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FFC6EFCE"/>'
        '<bgColor indexed="64"/></patternFill></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FFFFC7CE"/>'
        '<bgColor indexed="64"/></patternFill></fill>'
        "</fills>"
        '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
        '<cellStyleXfs count="1">'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>'
        "</cellStyleXfs>"
        '<cellXfs count="4">'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
        '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" '
        'applyFont="1" applyFill="1" applyAlignment="1">'
        '<alignment horizontal="center"/></xf>'
        '<xf numFmtId="0" fontId="2" fillId="3" borderId="0" xfId="0" applyFont="1" applyFill="1"/>'
        '<xf numFmtId="0" fontId="3" fillId="4" borderId="0" xfId="0" applyFont="1" applyFill="1"/>'
        "</cellXfs>"
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
        "</styleSheet>"
    )


def _details_row(result: ValidationResult) -> list[object]:
    return [
        result.participante,
        result.empresa,
        result.link,
        "OK" if result.status == LinkStatus.OK else "ERRO",
        result.status.value,
        result.rule_name or "",
        result.evidence or "",
        result.http_status if result.http_status is not None else "",
        result.final_url or "",
        round(result.response_time_seconds * 1000)
        if result.response_time_seconds is not None
        else "",
        result.technical_error or "",
    ]


def _ensure_can_write(path: Path, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(
            f"Arquivo de saida ja existe: {path}. Use --overwrite para substituir."
        )
