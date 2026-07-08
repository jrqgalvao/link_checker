# link-checker Documentation

Local desktop app for automating validation of unique event registration links.

This document also acts as a work guide for code agents, including OpenCode,
Deepseek v4 flash, and smaller models. Follow these rules before changing files.

## Project Goal

Open a local desktop window, validate a list of registration links, classify
each link through pluggable rules, and generate a final report.

Supported statuses:

- `OK`
- `INVALIDO_SUPORTE`
- `MORTO_404`
- `ERRO_HTTP`
- `TIMEOUT`
- `INDETERMINADO`
- `ERRO_TECNICO`

## Current State

The main project flow is the local desktop app.

Delivered:

- Input reading from operational Excel files without headers (`.xlsx`, `.xlsm`, `.xls`) and legacy CSV.
- HTTP validation with timeout, redirects, simple retry, and controlled parallelism.
- Pluggable classification rules with detailed internal status.
- Simple operational `.xlsx` or `.csv` report with final result `OK` or `ERROR`.
- Optional technical `.csv` report for debugging.
- Desktop app with spreadsheet selection, validation, KPIs, filters, search, and export.
- Unit tests for input reading, rules, HTTP checker, runner, CLI, reports, and UI API.
- Local PyInstaller build at `dist/LinkChecker/LinkChecker.exe`.

Still pending:

- Real validation with larger operational samples.
- Rule refinement using manually collected real HTML samples.
- Manual executable validation on final user machines.

## Fixed Structure

Do not reorganize folders unless explicitly requested.

```text
src/link_checker/
  checkers/      HTTP validation
  io/            input reading and report writing
  rules/         pluggable classification rules
  services/      validation orchestration
  ui/            pywebview desktop UI and UI API
  utils/         small shared utilities
  cli.py         technical command-line tool
  config.py      environment-based configuration
  enums.py       final statuses
  models.py      data models
  runner.py      shared validation flow without new business rules
tests/           offline unit tests
data/            sample input files
reports/         generated outputs
```

## GitHub Publishing Rules

For public publishing, use this `github/` folder.

This folder must contain only source code, tests, examples, and documentation.
Do not include:

- `dist/`
- `build/`
- caches (`__pycache__`, `.pytest_cache`, `.ruff_cache`)
- generated executables
- real operational reports
- real client/company brands, domains, or logos

In the public package:

- `README.md` is a short GitHub-facing project overview.
- `documentation.md` contains this detailed documentation.
- sample data must use placeholders such as `example.com` and `Sample Company`.
- logos must be generic placeholders.

## Rules For Code Agents And Smaller Models

Follow these rules literally. If unsure, stop and request review.

1. Do not change the architecture.
2. Do not create a monolithic solution.
3. Do not put file reading, validation, and report writing in the same module.
4. Do not move business rules to `cli.py`.
5. Do not move classification rules to `runner.py`, `input_reader.py`, or `report_writer.py`.
6. Do not add new dependencies without explicit approval.
7. Do not use the internet in tests.
8. Do not use real links in automated tests.
9. Do not reintroduce Playwright/browser checker without explicit approval.
10. Do not delete existing files without explicit request.
11. Do not create commits.
12. Do not change public names without updating tests and documentation.
13. Do not hide technical errors: propagate them to `ValidationResult.technical_error`.
14. Do not change rule order without a specific test.
15. Do not change the operational report format without explicit request.
16. Do not overwrite existing reports unless `--overwrite` is used.
17. Do not increase default `LINK_CHECKER_MAX_WORKERS` or retry count without operational justification.

Acceptable changes for smaller models:

- README/documentation copy edits.
- Small test for a clear bug.
- Error message fixes.
- Conservative term addition to an existing rule.
- `.env.example` changes when the equivalent field already exists in `config.py`.

Changes requiring human review or a stronger model:

- New dependency.
- New architecture.
- Parallelism, retry, browser automation, or business-rule changes.
- Input or output format changes.
- Changes to `ValidationResult`, `InputLinkRecord`, or `LinkStatus`.
- Changes to the main `LinkValidationService` flow.

## Where To Change Things

- New classification rule: `src/link_checker/rules/`
- Rule order: `src/link_checker/rules/registry.py`
- HTTP validation: `src/link_checker/checkers/http_checker.py`
- Main validation flow: `src/link_checker/services/link_validation_service.py`
- Input reading: `src/link_checker/io/input_reader.py`
- Report writing: `src/link_checker/io/report_writer.py`
- Fields and models: `src/link_checker/models.py`
- Statuses: `src/link_checker/enums.py`
- Configuration: `src/link_checker/config.py`
- CLI: `src/link_checker/cli.py`, only arguments, calls, and summary

## Where Not To Change Without Approval

- `src/link_checker/models.py`: changes internal contracts and technical report shape.
- `src/link_checker/enums.py`: changes statuses and can break classifications.
- `src/link_checker/services/link_validation_service.py`: changes decision flow.
- `src/link_checker/runner.py`: changes parallelism, ordering, and report writing.
- `pyproject.toml`: changes installation and dependencies.
- `data/sample_input.xlsx`: used as the operational example.

## Change Limits

Before editing, identify the smallest affected module.

Small changes should touch few files. Examples:

- Add a rule: 1 file in `rules/`, 1 registry update, 1 test.
- Add a report column: `models.py`, `report_writer.py` if needed, test.
- Change timeout or user agent: `config.py` or `.env.example`.
- Fix classification: specific rule and rule test.

Avoid:

- Factories, managers, or abstractions without more than one real implementation.
- Configuration for values that do not change yet.
- Duplicating rules across modules.
- Reintroducing heavy CSV/XLSX libraries without clear operational gain.
- Large end-to-end tests when a unit test covers the risk.

Current safety limits:

- `LINK_CHECKER_MAX_WORKERS=8` is the default for roughly 400 links.
- `LINK_CHECKER_HTTP_RETRY_COUNT=1` avoids excessive duplicate traffic.
- `LINK_CHECKER_HTTP_TIMEOUT_SECONDS=30` avoids hanging on slow links.
- Rule HTML text is capped at 100,000 characters.
- The operational report must stay simple: `OK` or `ERROR`.
- The technical report is where debugging details belong.

## Required Change Flow

1. Read the directly involved files.
2. Write or adjust a unit test before implementation when adding logic.
3. Implement the smallest code that solves the case.
4. Run the checks.
5. Summarize changed files and impact.

Test placement:

- Rule bug: `tests/test_*_rule.py`.
- HTTP bug: `tests/test_http_checker.py` with mocks, no internet.
- Input bug: `tests/test_input_reader.py`.
- Output bug: `tests/test_report_writer.py`.
- CLI bug: `tests/test_cli.py`.
- Orchestration/parallelism bug: `tests/test_runner.py`.

Checks:

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

Do not finalize changes if any command fails.

Technical CLI smoke test:

```powershell
python -m link_checker.cli --input data/sample_input.csv --output reports/result.csv
```

Operational Excel test:

```powershell
python -m link_checker.cli --input data/sample_input.xlsx --output reports/result.xlsx --technical-report reports/technical_result.csv --overwrite
```

## Installation

For end users, use the executable:

```text
dist/LinkChecker/LinkChecker.exe
```

Opening the executable should show a local desktop window. Users do not need to
open a browser, run a server, or install Python.

Main flow:

```text
Open LinkChecker.exe
Select spreadsheet
Validate
Export report
```

For development:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

The project is defined for Python 3.12+. The default install includes the
desktop UI.

Start the local desktop window in development:

```powershell
python -m link_checker.ui.app
```

Installed main script:

```powershell
link-checker
```

Secondary technical CLI:

```powershell
link-checker-cli --input data/sample_input.xlsx --output reports/result.xlsx --overwrite
```

Build the executable locally:

```powershell
python -m PyInstaller LinkChecker.spec
```

Expected output:

```text
dist/LinkChecker/LinkChecker.exe
```

## Desktop App

The app uses `pywebview`, opens a local window, and reuses the same validation
flow as the technical CLI. It does not create a separate business-rule layer,
does not open an external browser, and does not depend on a web server.

Spreadsheet reading and UI validation run in the background to keep the window
responsive. The screen polls progress in a controlled way, debounces search, and
paginates the table to avoid reprocessing all rows on every interaction.

Current flow:

1. Select a spreadsheet (`.xlsx`, `.xlsm`, `.xls`, or `.csv`).
2. The UI loads the file and shows the number of rows found.
3. Click `Validate`.
4. The screen shows KPIs and a results table.
5. Export the operational report by choosing where to save it.

Screen components:

- Sidebar with file selection, validation, clearing, and export.
- KPIs: total, ACTIVE, and INACTIVE.
- Quick filters: ALL, ACTIVE, and INACTIVE.
- Search by participant, company, link, or evidence.
- Main table with participant, company, link, and operational result.
- Export modal when filter/search is active, allowing all rows or visible rows.

UI output:

```text
path chosen by the user during export
```

The UI saves the operational report as `.xlsx`. The technical report remains
available through the technical CLI.

## Input

### Operational Excel Format

Accepts `.xlsx`, `.xlsm`, and `.xls`.

The spreadsheet **must not have a header**.

Columns by position:

```text
Column A -> PARTICIPANT NAME
Column B -> COMPANY NAME
Column C -> LINK
```

- Extra columns are ignored.
- Rows where the first three columns are all empty are ignored.
- Values are trimmed.
- If the first row contains an old header (`PARTICIPANT NAME`, etc.), reading fails with a clear error.
- If the first sheet is empty, reading fails with a clear error.
- If the first row looks like a title/comment before the data, reading fails with a clear error.

Sample file:

```text
data/sample_input.xlsx
```

Test reading without validating links:

```powershell
python -m link_checker.cli --dry-run --input data/sample_input.xlsx
```

Do not change the operational format without explicit request. The operational
Excel file has no header.

### Legacy CSV Format

Required columns:

```text
participante,email,empresa,evento_esperado,link
```

Sample file:

```text
data/sample_input.csv
```

## Output

The operational report can be generated as `.xlsx` or `.csv`.

`.xlsm` is not accepted as output to avoid confusion: generated reports do not
preserve macros.

The operational Excel file contains:

- `resultado` sheet: simple report with `OK`/`ERROR`
- `detalhes` sheet: internal status, rule, evidence, HTTP status, final URL, and technical error

Columns in the `resultado` sheet:

- `NOME DO PARTICIPANTE`
- `NOME DA EMPRESA`
- `LINK`
- `RESULTADO`

`RESULTADO` is:

- `OK` for a valid registration link
- `ERRO` for every other case (404, timeout, technical error, support page, etc.)

In Excel, the header and `RESULTADO` column are colored to make `OK` (green) and
`ERRO` (red) easy to identify.

Example:

```powershell
python -m link_checker.cli --input data/sample_input.xlsx --output reports/result.xlsx
```

For safety, existing output files are not overwritten by default. Use
`--overwrite` only when replacing previous reports intentionally.

Optional technical report for debugging:

```powershell
python -m link_checker.cli --input data/sample_input.xlsx --output reports/result.xlsx --technical-report reports/technical_result.csv
```

The technical file includes internal status, HTTP status, final URL, rule,
evidence, and technical error.

Do not put technical fields in the operational report. Use the technical report.

## How To Add A New Rule

1. Create a class in `src/link_checker/rules/`.
2. Implement `match(context) -> RuleMatch | None`.
3. Return `None` when the rule does not apply.
4. Return `RuleMatch` with status, rule name, and evidence when it applies.
5. Register the rule in `RuleRegistry` in the correct order.
6. Add a unit test for the rule.
7. If order matters, add an order test.

Rules must be conservative:

- False `OK` is worse than false `ERROR`.
- `OK` by strong URL is acceptable.
- `OK` by text requires strong signals.
- Generic pages must become `INDETERMINADO`.
- Timeout, technical error, and HTTP 4xx/5xx beat content rules.

Expected model:

```python
class MyRule:
    name = "my_rule"

    def match(self, context: ValidationContext) -> RuleMatch | None:
        if condition:
            return RuleMatch(LinkStatus.OK, self.name, "evidence")
        return None
```

## Current Decisions

- HTTP validation uses Python's standard library (`urllib`) with redirects and a default 30-second timeout per link.
  The timeout can be configured through `LINK_CHECKER_HTTP_TIMEOUT_SECONDS` in `.env`.
- Transient failures use simple retry configured by `LINK_CHECKER_HTTP_RETRY_COUNT`.
- Validation runs in parallel with `LINK_CHECKER_MAX_WORKERS` workers while preserving report order.
- Empty URLs or URLs without `http/https` become controlled technical errors before any request.
- HTML text used by rules is capped at 100,000 characters to reduce memory risk.
- Current HTTP classification:
  - 404 -> `MORTO_404`
  - other 4xx/5xx -> `ERRO_HTTP`
  - technical error without HTTP response -> `ERRO_TECNICO`
  - timeout -> `TIMEOUT`
  - HTTP 200 with strong support/error signals -> `INVALIDO_SUPORTE`
  - Strong signal examples: final URL `/controladora/erro/`, "Problemas com os dados de acesso", "link invalido", "acesso invalido"
  - `SupportErrorRule` must be conservative: "entre em contato", "erro", and "suporte" do not classify an error by themselves.
  - False `OK` is bad, but false `ERROR` on a valid page also hurts operations.
  - Registration page classification:
    - Normal HTTP with final URL `/hotsite/inscricoes-participantes/form/` or `/inscricoes-participantes/form/` -> `OK`
    - Normal HTTP with clear text containing `inscricao` and `participante` -> `OK`
    - Generic HTTP 200 without strong signals -> `INDETERMINADO`
- Operational CSV uses the standard library; operational Excel uses `openpyxl`; legacy `.xls` uses `xlrd`.
- Configuration uses `dataclass` and `LINK_CHECKER_*` variables, with simple `.env` support.
- `pytest` covers rules and services without internet access.
- The main flow is HTTP-only. Browser checker/Playwright are not part of the current core.

## Delivery Checklist

- Folder structure stayed the same.
- No new dependency was added without approval.
- A new test failed before implementation when new logic was added.
- `python -m pytest` passed.
- `python -m ruff check .` passed.
- `python -m ruff format --check .` passed.
- Documentation was updated if behavior, commands, config, or formats changed.
- No real links were used in automated tests.
- No internet calls were made in tests.
- Operational report stayed simple.
- Technical report stayed optional.

## Common Mistakes To Avoid

- Classifying `OK` only because the word `evento` appears.
- Classifying `OK` only because the word `participante` appears.
- Classifying `OK` only because the word `inscricao` appears.
- Classifying `ERROR` only because the word `suporte` appears in a footer.
- Putting technical details in the operational report.
- Testing with real URLs.
- Increasing parallelism "to make it faster" without measuring.
- Reintroducing Playwright/browser checker without an explicit product decision.
- Removing legacy CSV support without explicit request.
- Recreating the architecture instead of fixing the right module.

## Allowed Next Steps

- More rules based on manually collected real HTML.
- Report improvements when there is a clear operational need.

Any change outside these limits must be proposed before implementation.
