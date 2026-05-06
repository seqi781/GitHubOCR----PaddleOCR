from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from gh_ocr_paddle_agent.core.config import EVAL_DIR, FIXTURES_DIR
from gh_ocr_paddle_agent.core.models import EvalCaseResult, EvalReport
from gh_ocr_paddle_agent.graph.workflow import run_migration


def evaluate_fixtures() -> Path:
    cases_root = FIXTURES_DIR / "repos"
    expectations_root = FIXTURES_DIR / "expectations"
    EVAL_DIR.mkdir(parents=True, exist_ok=True)

    case_results: list[EvalCaseResult] = []
    for repo_dir in sorted(path for path in cases_root.iterdir() if path.is_dir()):
        expectation_path = expectations_root / f"{repo_dir.name}.json"
        expectation = json.loads(expectation_path.read_text(encoding="utf-8"))
        state = run_migration(str(repo_dir), output_dir=str(EVAL_DIR / repo_dir.name))
        detected = sorted(state.plan.source_stack if state.plan else [])
        expected = sorted(expectation["expected_stack"])

        checks = [
            detected == expected,
            state.verification.passed if state.verification else False,
            (Path(state.output_dir) / "migration_report.md").exists(),
        ]
        score = sum(1 for item in checks if item) / len(checks)
        notes = []
        if detected != expected:
            notes.append(f"Detected stack mismatch: expected={expected} got={detected}")
        if state.plan and state.plan.confidence < 0.5:
            notes.append("Low migration confidence.")
        case_results.append(
            EvalCaseResult(
                case_name=repo_dir.name,
                passed=all(checks),
                detected_stack=detected,
                expected_stack=expected,
                score=round(score, 2),
                notes=notes,
            )
        )

    average_score = sum(case.score for case in case_results) / max(len(case_results), 1)
    report = EvalReport(
        created_at=datetime.utcnow().isoformat(),
        total_cases=len(case_results),
        passed_cases=sum(1 for case in case_results if case.passed),
        average_score=round(average_score, 2),
        case_results=case_results,
    )
    target = EVAL_DIR / "latest_eval_report.json"
    target.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return target

