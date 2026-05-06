from __future__ import annotations

from pathlib import Path

from gh_ocr_paddle_agent.core.models import VerificationResult


def verify_run(output_dir: str) -> VerificationResult:
    root = Path(output_dir)
    rewritten_root = root / "rewritten_repo"
    checks = {
        "rewritten_repo_exists": rewritten_root.exists(),
        "requirements_present": (rewritten_root / "requirements.txt").exists(),
        "paddle_support_present": (rewritten_root / "migration_support" / "paddle_ocr_engine.py").exists(),
        "report_present": (root / "migration_report.md").exists(),
        "patch_present": (root / "patches" / "suggested_changes.diff").exists(),
    }
    score = sum(1 for passed in checks.values() if passed) / len(checks)
    notes = []
    if not checks["requirements_present"]:
        notes.append("requirements.txt was not generated.")
    if not checks["paddle_support_present"]:
        notes.append("PaddleOCR helper wrapper is missing.")
    return VerificationResult(
        passed=all(checks.values()),
        score=round(score, 2),
        checks=checks,
        notes=notes,
    )

