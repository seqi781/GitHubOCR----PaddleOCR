from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
OUTPUTS_DIR = ROOT_DIR / "outputs"
RUNS_DIR = OUTPUTS_DIR / "runs"
EVAL_DIR = OUTPUTS_DIR / "evaluations"
FIXTURES_DIR = ROOT_DIR / "fixtures"

