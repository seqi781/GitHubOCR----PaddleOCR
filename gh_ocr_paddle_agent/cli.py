from __future__ import annotations

import argparse
from pathlib import Path

from gh_ocr_paddle_agent.core.evaluation import evaluate_fixtures
from gh_ocr_paddle_agent.graph.workflow import run_migration


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GitHub OCR -> PaddleOCR migration agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    migrate = subparsers.add_parser("migrate", help="Migrate a repository to a PaddleOCR-oriented scaffold")
    migrate.add_argument("--source", required=True, help="GitHub repository URL or local path")
    migrate.add_argument("--output-dir", default=None, help="Directory where run artifacts will be written")

    subparsers.add_parser("evaluate", help="Run fixture-based evaluation")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "migrate":
        state = run_migration(args.source, args.output_dir)
        print(f"run_id={state.run_id}")
        print(f"output_dir={state.output_dir}")
        print(f"detected_stack={state.plan.source_stack if state.plan else []}")
        print(f"verification={state.verification.model_dump() if state.verification else {}}")
        return

    if args.command == "evaluate":
        report = evaluate_fixtures()
        print(f"evaluation_report={report}")
        return


if __name__ == "__main__":
    main()
