from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from link_checker.checkers.http_checker import HttpChecker
from link_checker.config import Settings
from link_checker.enums import LinkStatus
from link_checker.io.input_reader import InputReader
from link_checker.io.report_writer import ReportWriter
from link_checker.models import ValidationResult
from link_checker.rules.registry import RuleRegistry
from link_checker.services.link_validation_service import LinkValidationService


def validate_file(
    input_path: Path,
    settings: Settings | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
) -> list[ValidationResult]:
    settings = settings or Settings()
    checker = HttpChecker(
        timeout_seconds=settings.http_timeout_seconds,
        user_agent=settings.user_agent,
        max_redirects=settings.max_redirects,
        retry_count=settings.http_retry_count,
    )
    service = LinkValidationService(
        http_checker=checker,
        rule_registry=RuleRegistry(),
    )
    records = InputReader().read(input_path)
    total = len(records)

    if settings.max_workers > 1 and total > 1:
        with ThreadPoolExecutor(max_workers=settings.max_workers) as executor:
            future_to_idx = {
                executor.submit(service.validate, record): i for i, record in enumerate(records)
            }
            results: list[ValidationResult] = [None] * total  # type: ignore[list-item]
            completed = 0
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                results[idx] = future.result()
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)
            return results

    results = []
    for idx, record in enumerate(records):
        results.append(service.validate(record))
        if progress_callback:
            progress_callback(idx + 1, total)
    return results


def run(
    input_path: Path,
    output_path: Path,
    settings: Settings | None = None,
    technical_output_path: Path | None = None,
    overwrite: bool = False,
) -> Counter[LinkStatus]:
    settings = settings or Settings()
    results = validate_file(input_path, settings)
    writer = ReportWriter()
    writer.write(results, output_path, overwrite=overwrite)
    if technical_output_path:
        writer.write_technical(results, technical_output_path, overwrite=overwrite)
    return Counter(result.status for result in results)
