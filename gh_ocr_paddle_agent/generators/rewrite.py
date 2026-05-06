from __future__ import annotations

import difflib
import shutil
from pathlib import Path

from gh_ocr_paddle_agent.core.models import GeneratedArtifact, MigrationPlan, RepositoryProfile
from gh_ocr_paddle_agent.generators.paddle_template import write_support_files


def _rewrite_requirements(text: str) -> str:
    lines = text.splitlines()
    rewritten: list[str] = []
    replaced = False
    for line in lines:
        lower = line.strip().lower()
        if any(pkg in lower for pkg in ("pytesseract", "easyocr", "keras-ocr", "python-doctr")):
            if not replaced:
                rewritten.append("paddleocr")
                replaced = True
            continue
        rewritten.append(line)
    if not replaced and "paddleocr" not in "\n".join(rewritten).lower():
        rewritten.append("paddleocr")
    return "\n".join(rewritten).strip() + "\n"


def _rewrite_python_source(text: str) -> str:
    new_text = text
    if "import pytesseract" in new_text or "from pytesseract" in new_text:
        new_text = new_text.replace("import pytesseract", "from migration_support.paddle_ocr_engine import extract_text")
        new_text = new_text.replace("from pytesseract import image_to_string", "from migration_support.paddle_ocr_engine import extract_text")
        new_text = new_text.replace("pytesseract.image_to_string", "extract_text")

    if "easyocr.Reader" in new_text or "import easyocr" in new_text:
        new_text = new_text.replace("import easyocr", "from migration_support.paddle_ocr_engine import extract_text")
        new_text = new_text.replace("from easyocr import Reader", "from migration_support.paddle_ocr_engine import extract_text")
        new_text = new_text.replace("reader = easyocr.Reader(['en'])", "# TODO: configure PaddleOCR language in migration_support/paddle_ocr_engine.py")
        new_text = new_text.replace("Reader(['en'])", "extract_text")
        new_text = new_text.replace(".readtext(", "(")
    return new_text


def rewrite_repository(
    profile: RepositoryProfile,
    plan: MigrationPlan,
    output_dir: str,
) -> list[GeneratedArtifact]:
    source_root = Path(profile.local_path)
    run_root = Path(output_dir)
    rewritten_root = run_root / "rewritten_repo"
    patches_root = run_root / "patches"

    if rewritten_root.exists():
        shutil.rmtree(rewritten_root)
    shutil.copytree(source_root, rewritten_root, dirs_exist_ok=True)
    patches_root.mkdir(parents=True, exist_ok=True)

    artifacts: list[GeneratedArtifact] = [
        GeneratedArtifact(path=str(rewritten_root), kind="directory", description="Rewritten repository copy."),
        GeneratedArtifact(path=str(patches_root), kind="directory", description="Suggested diff patches."),
    ]

    diff_chunks: list[str] = []
    for py_file in sorted(rewritten_root.rglob("*.py")):
        old = py_file.read_text(encoding="utf-8", errors="ignore")
        new = _rewrite_python_source(old)
        if new != old:
            py_file.write_text(new, encoding="utf-8")
            diff = difflib.unified_diff(
                old.splitlines(),
                new.splitlines(),
                fromfile=str(py_file.relative_to(rewritten_root)),
                tofile=str(py_file.relative_to(rewritten_root)),
                lineterm="",
            )
            diff_chunks.extend(list(diff))

    requirements_file = rewritten_root / "requirements.txt"
    if requirements_file.exists():
        old = requirements_file.read_text(encoding="utf-8", errors="ignore")
    else:
        old = ""
    new = _rewrite_requirements(old)
    requirements_file.write_text(new, encoding="utf-8")
    diff = difflib.unified_diff(
        old.splitlines(),
        new.splitlines(),
        fromfile="requirements.txt",
        tofile="requirements.txt",
        lineterm="",
    )
    diff_chunks.extend(list(diff))

    for support_file in write_support_files(rewritten_root):
        artifacts.append(
            GeneratedArtifact(
                path=str(support_file),
                kind="file",
                description="Generated PaddleOCR support file.",
            )
        )

    report_path = run_root / "migration_report.md"
    report_path.write_text(_build_report(profile, plan), encoding="utf-8")
    artifacts.append(
        GeneratedArtifact(path=str(report_path), kind="report", description="Migration report.")
    )

    patch_file = patches_root / "suggested_changes.diff"
    patch_file.write_text("\n".join(diff_chunks).strip() + "\n", encoding="utf-8")
    artifacts.append(
        GeneratedArtifact(path=str(patch_file), kind="patch", description="Suggested source diff.")
    )
    return artifacts


def _build_report(profile: RepositoryProfile, plan: MigrationPlan) -> str:
    lines = [
        "# Migration Report",
        "",
        f"- Source: `{profile.source}`",
        f"- Local Path: `{profile.local_path}`",
        f"- Detected OCR Stack: `{', '.join(plan.source_stack) or 'none'}`",
        f"- Confidence: `{plan.confidence}`",
        "",
        "## Proposed Changes",
        "",
    ]
    lines.extend(f"- {change}" for change in plan.changes)
    lines.extend(["", "## Risks", ""])
    lines.extend(f"- {risk}" for risk in plan.risks)
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {step}" for step in plan.next_steps)
    return "\n".join(lines) + "\n"

