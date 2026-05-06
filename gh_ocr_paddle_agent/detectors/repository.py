from __future__ import annotations

from pathlib import Path

from gh_ocr_paddle_agent.core.models import RepositoryProfile


DEPENDENCY_FILES = (
    "requirements.txt",
    "pyproject.toml",
    "Pipfile",
)


def scan_repository(source: str, local_repo_path: str) -> RepositoryProfile:
    root = Path(local_repo_path)
    python_files = sorted(
        str(path.relative_to(root))
        for path in root.rglob("*.py")
        if ".venv" not in path.parts and "__pycache__" not in path.parts
    )

    dependencies: list[str] = []
    for filename in DEPENDENCY_FILES:
        dependency_file = root / filename
        if dependency_file.exists():
            dependencies.extend(dependency_file.read_text(encoding="utf-8").splitlines())

    return RepositoryProfile(
        source=source,
        local_path=str(root),
        file_count=sum(1 for _ in root.rglob("*") if _.is_file()),
        python_files=python_files,
        dependencies=dependencies,
    )

