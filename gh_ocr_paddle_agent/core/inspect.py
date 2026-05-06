from __future__ import annotations

from pathlib import Path


def list_text_files(root: Path, limit: int = 50) -> list[Path]:
    results: list[Path] = []
    if not root.exists():
        return results
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in {".git", "__pycache__", ".venv"} for part in path.parts):
            continue
        results.append(path)
        if len(results) >= limit:
            break
    return results


def read_text_excerpt(path: Path, max_chars: int = 6000) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return f"[read error] {exc}"
    return text[:max_chars]
