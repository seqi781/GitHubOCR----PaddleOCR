from __future__ import annotations

from pathlib import Path

from gh_ocr_paddle_agent.core.models import MigrationPlan, RepositoryProfile


SIGNATURES: dict[str, tuple[str, ...]] = {
    "pytesseract": (
        "import pytesseract",
        "from pytesseract",
        "image_to_string(",
    ),
    "easyocr": (
        "import easyocr",
        "from easyocr",
        "easyocr.Reader(",
        "readtext(",
    ),
    "keras_ocr": (
        "import keras_ocr",
        "keras_ocr.pipeline.Pipeline(",
    ),
    "doctr": (
        "from doctr",
        "import doctr",
    ),
}


def detect_ocr_stack(profile: RepositoryProfile) -> tuple[RepositoryProfile, MigrationPlan]:
    root = Path(profile.local_path)
    matched: dict[str, list[str]] = {}

    for rel_path in profile.python_files:
        file_path = root / rel_path
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        for engine, signatures in SIGNATURES.items():
            hits = [signature for signature in signatures if signature in text]
            if hits:
                matched.setdefault(engine, []).append(rel_path)

    profile.matched_signatures = matched

    source_stack = sorted(matched)
    confidence = 0.25 + 0.25 * len(source_stack)
    if source_stack:
        confidence = min(confidence, 0.95)

    changes = [
        "Replace source OCR package dependencies with `paddleocr`.",
        "Add a reusable PaddleOCR service wrapper for Python call sites.",
        "Generate a rewritten repository copy and a diff-style suggestion report.",
    ]
    risks = [
        "Dynamic OCR call patterns may require manual follow-up after automatic migration.",
        "Training, detection, and layout-analysis code usually needs human verification.",
    ]
    next_steps = [
        "Install `paddleocr` in the rewritten project environment.",
        "Run smoke tests against sample images or existing OCR fixtures.",
        "Review the generated diff before merging into production.",
    ]
    if not source_stack:
        risks.insert(0, "No known OCR library was detected; migration output is a best-effort scaffold.")

    plan = MigrationPlan(
        source_stack=source_stack,
        changes=changes,
        risks=risks,
        next_steps=next_steps,
        confidence=round(confidence, 2),
    )
    return profile, plan

