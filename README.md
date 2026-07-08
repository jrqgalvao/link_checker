# Link Checker

Local desktop app for validating spreadsheet-based registration links in bulk.

The app reads `.xlsx`, `.xlsm`, `.xls`, or `.csv` files, checks links with
timeout, retry, redirects, and controlled parallelism, classifies each result,
and exports a simple operational Excel report.

## Features

- Desktop UI with spreadsheet upload, filters, search, and export.
- HTTP validation using Python's standard library.
- Pluggable classification rules.
- Simple operational report with `OK` or `ERROR`.
- Optional technical report through the CLI.
- Unit tests that do not use the internet or real links.

## Documentation

Detailed documentation is available in [documentation.md](documentation.md).

## Development Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m link_checker.ui.app
```

## Checks

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

## Build

```powershell
python -m PyInstaller LinkChecker.spec
```

The executable is generated at:

```text
dist/LinkChecker/LinkChecker.exe
```
