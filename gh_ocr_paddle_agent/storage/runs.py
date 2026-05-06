from __future__ import annotations

import json
from pathlib import Path

from gh_ocr_paddle_agent.core.models import RunSummary


def persist_summary(summary: RunSummary, output_dir: str) -> Path:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    target = root / "migration_summary.json"
    target.write_text(summary.model_dump_json(indent=2), encoding="utf-8")
    return target


def persist_failed_run(payload: dict, output_dir: str) -> Path:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    target = root / "migration_summary.json"
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return target


def load_summaries(runs_root: Path) -> list[dict]:
    results: list[dict] = []
    for path in sorted(runs_root.glob("*/migration_summary.json"), reverse=True):
        try:
            results.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return results
