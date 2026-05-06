from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


class RepositoryProfile(BaseModel):
    source: str
    local_path: str
    language: str = "python"
    file_count: int = 0
    python_files: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    matched_signatures: dict[str, list[str]] = Field(default_factory=dict)


class MigrationPlan(BaseModel):
    source_stack: list[str] = Field(default_factory=list)
    target_stack: list[str] = Field(default_factory=lambda: ["paddleocr"])
    changes: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class GeneratedArtifact(BaseModel):
    path: str
    kind: Literal["file", "directory", "report", "patch"]
    description: str


class VerificationResult(BaseModel):
    passed: bool
    score: float
    checks: dict[str, bool] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)


class RunSummary(BaseModel):
    run_id: str
    source: str
    output_dir: str
    repository: RepositoryProfile
    plan: MigrationPlan
    artifacts: list[GeneratedArtifact] = Field(default_factory=list)
    verification: VerificationResult
    logs: list[str] = Field(default_factory=list)
    error: str | None = None


class EvalCaseResult(BaseModel):
    case_name: str
    passed: bool
    detected_stack: list[str]
    expected_stack: list[str]
    score: float
    notes: list[str] = Field(default_factory=list)


class EvalReport(BaseModel):
    created_at: str
    total_cases: int
    passed_cases: int
    average_score: float
    case_results: list[EvalCaseResult] = Field(default_factory=list)


class MigrationState(BaseModel):
    run_id: str
    source: str
    output_dir: str
    local_repo_path: str = ""
    repository: RepositoryProfile | None = None
    plan: MigrationPlan | None = None
    artifacts: list[GeneratedArtifact] = Field(default_factory=list)
    verification: VerificationResult | None = None
    logs: list[str] = Field(default_factory=list)
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump()
