from __future__ import annotations

import subprocess
import shutil
from pathlib import Path


def resolve_source(source: str, work_dir: Path) -> Path:
    if source.startswith("http://") or source.startswith("https://") or source.endswith(".git"):
        target = work_dir / "source_repo"
        if target.exists():
            shutil.rmtree(target)
        subprocess.run(
            ["git", "clone", "--depth", "1", source, str(target)],
            check=True,
            capture_output=True,
            text=True,
        )
        return target
    local = Path(source).expanduser().resolve()
    if not local.exists():
        raise FileNotFoundError(f"Source path does not exist: {local}")
    return local
