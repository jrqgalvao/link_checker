# Link Checker
Local desktop app for automating the validation of unique event registration links in bulk.
Manually checking hundreds of registration links one by one to confirm they still work is slow and error-prone. Link Checker reads a spreadsheet of links, validates each one automatically, classifies the result, and exports a simple operational report showing exactly which links are `OK` and which need attention.
The app reads `.xlsx`, `.xlsm`, `.xls`, or `.csv` files, checks links with
timeout, retry, redirects, and controlled parallelism, classifies each result,
and exports a simple operational Excel report.
## Features
- Desktop UI with spreadsheet upload, filters, search, and export.
- HTTP validation using Python's standard library.
- Pluggable classification rules.
- Simple operational report with `OK` or `ERRO`.
- UI actions wait for the desktop API before becoming available.
- Invalid numeric configuration fails early with a clear message.
- Rule failures are isolated to the affected link instead of aborting the batch.
- Optional technical report through the CLI.
- Unit tests that do not use the internet or real links.
## Documentation
Detailed documentation is available in [documentation.md](documentation.md).
## Installation
Clone the repository:
```powershell
git clone https://github.com/jrqgalvao/link_checker.git
cd link_checker
```
## Development Quick Start
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m link_checker.ui.app
```
The project requires Python 3.12+. The default install includes the desktop UI.
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
This is an onedir build: keep `LinkChecker.exe` together with its `_internal`
folder. For end users, it opens a local desktop window directly.
No browser, server, or Python installation is required.
