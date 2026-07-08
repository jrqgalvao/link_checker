from __future__ import annotations

import argparse
import sys
from pathlib import Path

from link_checker.config import Settings
from link_checker.enums import LinkStatus
from link_checker.io.input_reader import InputReader
from link_checker.logging_config import configure_logging
from link_checker.runner import run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Valida links unicos de inscricao em eventos.")
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Arquivo de entrada (.csv, .xlsx, .xlsm, .xls).",
    )
    parser.add_argument("--output", type=Path, help="Arquivo de relatorio de saida.")
    parser.add_argument(
        "--technical-report",
        type=Path,
        help="Arquivo opcional com status interno e evidencias tecnicas.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas le o arquivo de entrada e exibe a quantidade de registros.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Substitui relatorios existentes.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    try:
        if args.dry_run:
            reader = InputReader()
            records = reader.read(args.input)
            print(f"Registros lidos: {len(records)}")
            return

        if not args.output:
            build_parser().error("--output e obrigatorio quando --dry-run nao e fornecido.")

        settings = Settings()
        configure_logging(settings.debug)
        summary = run(
            args.input,
            args.output,
            settings,
            technical_output_path=args.technical_report,
            overwrite=args.overwrite,
        )
    except (FileExistsError, FileNotFoundError, ValueError, OSError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    print(f"total processado: {sum(summary.values())}")
    for status in (
        LinkStatus.OK,
        LinkStatus.INVALIDO_SUPORTE,
        LinkStatus.MORTO_404,
        LinkStatus.ERRO_HTTP,
        LinkStatus.TIMEOUT,
        LinkStatus.ERRO_TECNICO,
        LinkStatus.INDETERMINADO,
    ):
        print(f"{status.value}: {summary.get(status, 0)}")


if __name__ == "__main__":
    main()
