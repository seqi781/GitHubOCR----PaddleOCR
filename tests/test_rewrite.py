from pathlib import Path

from gh_ocr_paddle_agent.core.verification import verify_run
from gh_ocr_paddle_agent.detectors.ocr_stack import detect_ocr_stack
from gh_ocr_paddle_agent.detectors.repository import scan_repository
from gh_ocr_paddle_agent.generators.rewrite import rewrite_repository


def test_rewrite_generates_paddle_support(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "app.py").write_text("import pytesseract\ntext = pytesseract.image_to_string('img.png')\n")
    (repo / "requirements.txt").write_text("pytesseract\n")

    profile = scan_repository(str(repo), str(repo))
    profile, plan = detect_ocr_stack(profile)
    output_dir = tmp_path / "run"
    rewrite_repository(profile, plan, str(output_dir))

    rewritten = output_dir / "rewritten_repo"
    assert (rewritten / "migration_support" / "paddle_ocr_engine.py").exists()
    assert "paddleocr" in (rewritten / "requirements.txt").read_text()
    verification = verify_run(str(output_dir))
    assert verification.passed

