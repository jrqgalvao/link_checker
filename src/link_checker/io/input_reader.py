from __future__ import annotations

import csv
import zipfile
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree

from link_checker.models import InputLinkRecord

_SUPPORTED_EXCEL_EXTENSIONS = {".xlsx", ".xlsm", ".xls"}
_REQUIRED_CSV_COLUMNS = ("participante", "email", "empresa", "evento_esperado", "link")
_NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


class InputReader:
    def read(self, path: Path) -> list[InputLinkRecord]:
        if not path.exists():
            raise FileNotFoundError(f"Arquivo nao encontrado: {path}")

        suffix = path.suffix.lower()

        if suffix == ".csv":
            return self._read_csv(path)
        if suffix in _SUPPORTED_EXCEL_EXTENSIONS:
            return self._read_excel(path, suffix)
        raise ValueError(f"Extensao nao suportada: {suffix}. Use .csv, .xlsx, .xlsm ou .xls.")

    def _read_csv(self, path: Path) -> list[InputLinkRecord]:
        with path.open(newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            missing = [col for col in _REQUIRED_CSV_COLUMNS if col not in (reader.fieldnames or [])]
            if missing:
                raise ValueError(f"Colunas obrigatorias ausentes: {', '.join(missing)}")
            return [
                InputLinkRecord(
                    participante=str(row.get("participante") or "").strip(),
                    email=str(row.get("email") or "").strip(),
                    empresa=str(row.get("empresa") or "").strip(),
                    evento_esperado=str(row.get("evento_esperado") or "").strip(),
                    link=str(row.get("link") or "").strip(),
                )
                for row in reader
            ]

    def _read_excel(self, path: Path, suffix: str) -> list[InputLinkRecord]:
        try:
            rows = _read_xls_rows(path) if suffix == ".xls" else _read_xlsx_rows(path)
        except Exception as exc:
            raise ValueError(f"Nao foi possivel ler a planilha Excel: {exc}") from exc

        if not rows:
            raise ValueError("Planilha Excel vazia na primeira aba.")

        width = max(len(row) for row in rows)
        if width < 3:
            raise ValueError(
                "Planilha Excel deve ter pelo menos 3 colunas: "
                "nome do participante, nome da empresa e link."
            )

        first_row = [_cell(rows[0], i).lower() for i in range(3)]
        if first_row[0].startswith("nome") and first_row[2] == "link":
            raise ValueError(
                "A planilha Excel nao deve ter cabecalho. Remova a primeira linha de cabecalho."
            )

        if self._looks_like_title_row(rows):
            raise ValueError(
                "A primeira linha parece titulo ou observacao, nao um registro operacional."
            )

        records: list[InputLinkRecord] = []
        for row in rows:
            participante = _cell(row, 0)
            empresa = _cell(row, 1)
            link = _cell(row, 2)

            if not participante and not empresa and not link:
                continue

            records.append(
                InputLinkRecord(
                    participante=participante,
                    email="",
                    empresa=empresa,
                    evento_esperado="",
                    link=link,
                )
            )

        if not records:
            raise ValueError("Planilha Excel vazia.")

        return records

    @staticmethod
    def _looks_like_title_row(rows: list[list[object]]) -> bool:
        if len(rows) < 2:
            return False
        first_link = _cell(rows[0], 2)
        second_link = _cell(rows[1], 2)
        return not _has_http_scheme(first_link) and _has_http_scheme(second_link)


def _read_xlsx_rows(path: Path) -> list[list[object]]:
    with zipfile.ZipFile(path) as archive:
        shared_strings = _read_shared_strings(archive)
        sheet_xml = archive.read("xl/worksheets/sheet1.xml")

    root = ElementTree.fromstring(sheet_xml)
    rows: list[list[object]] = []
    for row_node in root.findall(".//x:sheetData/x:row", _NS):
        row: list[object] = []
        for cell in row_node.findall("x:c", _NS):
            column_index = _column_index(cell.attrib.get("r", "A1"))
            while len(row) <= column_index:
                row.append("")
            row[column_index] = _cell_value(cell, shared_strings)
        rows.append(row)
    return rows


def _read_xls_rows(path: Path) -> list[list[object]]:
    import xlrd

    sheet = xlrd.open_workbook(path).sheet_by_index(0)
    return [sheet.row_values(index) for index in range(sheet.nrows)]


def _cell(row: list[object], index: int) -> str:
    if index >= len(row):
        return ""
    return str(row[index] or "").strip()


def _read_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    return [
        "".join(text.text or "" for text in item.findall(".//x:t", _NS))
        for item in root.findall("x:si", _NS)
    ]


def _cell_value(cell: ElementTree.Element, shared_strings: list[str]) -> str:
    if cell.attrib.get("t") == "inlineStr":
        return "".join(text.text or "" for text in cell.findall(".//x:t", _NS))

    value = cell.find("x:v", _NS)
    if value is None or value.text is None:
        return ""
    if cell.attrib.get("t") == "s":
        index = int(value.text)
        return shared_strings[index] if index < len(shared_strings) else ""
    return value.text


def _column_index(cell_ref: str) -> int:
    letters = "".join(char for char in cell_ref if char.isalpha())
    index = 0
    for char in letters:
        index = index * 26 + ord(char.upper()) - ord("A") + 1
    return max(index - 1, 0)


def _has_http_scheme(value: str) -> bool:
    return urlparse(value).scheme in {"http", "https"}
