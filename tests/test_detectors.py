from gh_ocr_paddle_agent.detectors.ocr_stack import detect_ocr_stack
from gh_ocr_paddle_agent.detectors.repository import scan_repository


def test_detects_pytesseract_stack(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "main.py").write_text("import pytesseract\nprint(pytesseract.image_to_string('a.png'))\n")
    profile = scan_repository(str(repo), str(repo))
    profile, plan = detect_ocr_stack(profile)
    assert "pytesseract" in plan.source_stack
    assert profile.matched_signatures["pytesseract"] == ["main.py"]

