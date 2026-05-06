from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TypedDict
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from gh_ocr_paddle_agent.core.config import RUNS_DIR
from gh_ocr_paddle_agent.core.models import MigrationState, RunSummary
from gh_ocr_paddle_agent.core.source import resolve_source
from gh_ocr_paddle_agent.core.verification import verify_run
from gh_ocr_paddle_agent.detectors.ocr_stack import detect_ocr_stack
from gh_ocr_paddle_agent.detectors.repository import scan_repository
from gh_ocr_paddle_agent.generators.rewrite import rewrite_repository
from gh_ocr_paddle_agent.storage.runs import persist_failed_run, persist_summary


class WorkflowState(TypedDict, total=False):
    run_id: str
    source: str
    output_dir: str
    local_repo_path: str
    repository: dict
    plan: dict
    artifacts: list[dict]
    verification: dict
    logs: list[str]
    status: str
    error: str | None


def build_graph():
    graph = StateGraph(WorkflowState)
    graph.add_node("resolve_source", _resolve_source)
    graph.add_node("inventory_repository", _inventory_repository)
    graph.add_node("detect_ocr_stack", _detect_ocr_stack)
    graph.add_node("rewrite_repository", _rewrite_repository)
    graph.add_node("verify_output", _verify_output)
    graph.add_node("persist_run", _persist_run)

    graph.add_edge(START, "resolve_source")
    graph.add_edge("resolve_source", "inventory_repository")
    graph.add_edge("inventory_repository", "detect_ocr_stack")
    graph.add_edge("detect_ocr_stack", "rewrite_repository")
    graph.add_edge("rewrite_repository", "verify_output")
    graph.add_edge("verify_output", "persist_run")
    graph.add_edge("persist_run", END)
    return graph.compile()


def create_initial_state(source: str, output_dir: str | None = None) -> MigrationState:
    run_id = datetime.utcnow().strftime("%Y%m%d%H%M%S") + "-" + uuid4().hex[:8]
    final_output_dir = Path(output_dir or RUNS_DIR / run_id)
    return MigrationState(
        run_id=run_id,
        source=source,
        output_dir=str(final_output_dir),
        status="running",
        logs=["Workflow initialized"],
    )


def run_migration(source: str, output_dir: str | None = None) -> MigrationState:
    state = create_initial_state(source, output_dir)
    app = build_graph()
    try:
        final_state = app.invoke(state.model_dump())
        final_model = MigrationState.model_validate(final_state)
        return final_model.model_copy(update={"status": "completed"})
    except Exception as exc:
        failed_state = state.model_copy(
            update={
                "status": "failed",
                "error": str(exc),
                "logs": state.logs + [f"Workflow failed: {exc}"],
            }
        )
        persist_failed_run(failed_state.model_dump(mode="json"), failed_state.output_dir)
        return failed_state


def _resolve_source(raw_state: WorkflowState) -> dict:
    state = MigrationState.model_validate(raw_state)
    run_root = Path(state.output_dir)
    run_root.mkdir(parents=True, exist_ok=True)
    local_repo = resolve_source(state.source, run_root)
    return {
        "local_repo_path": str(local_repo),
        "logs": state.logs + [f"Resolved source into {local_repo}"],
    }


def _inventory_repository(raw_state: WorkflowState) -> dict:
    state = MigrationState.model_validate(raw_state)
    profile = scan_repository(state.source, state.local_repo_path)
    return {
        "repository": profile,
        "logs": state.logs + [f"Scanned repository with {profile.file_count} files"],
    }


def _detect_ocr_stack(raw_state: WorkflowState) -> dict:
    state = MigrationState.model_validate(raw_state)
    assert state.repository is not None
    profile, plan = detect_ocr_stack(state.repository)
    return {
        "repository": profile,
        "plan": plan,
        "logs": state.logs + [f"Detected OCR stack: {plan.source_stack or ['unknown']}"],
    }


def _rewrite_repository(raw_state: WorkflowState) -> dict:
    state = MigrationState.model_validate(raw_state)
    assert state.repository is not None
    assert state.plan is not None
    artifacts = rewrite_repository(state.repository, state.plan, state.output_dir)
    return {
        "artifacts": artifacts,
        "logs": state.logs + [f"Generated {len(artifacts)} artifacts"],
    }


def _verify_output(raw_state: WorkflowState) -> dict:
    state = MigrationState.model_validate(raw_state)
    verification = verify_run(state.output_dir)
    return {
        "verification": verification,
        "logs": state.logs + [f"Verification passed={verification.passed} score={verification.score}"],
    }


def _persist_run(raw_state: WorkflowState) -> dict:
    state = MigrationState.model_validate(raw_state)
    assert state.repository is not None
    assert state.plan is not None
    assert state.verification is not None
    summary = RunSummary(
        run_id=state.run_id,
        source=state.source,
        output_dir=state.output_dir,
        repository=state.repository,
        plan=state.plan,
        artifacts=state.artifacts,
        verification=state.verification,
        logs=state.logs + ["Persisted migration summary JSON"],
        error=state.error,
    )
    persist_summary(summary, state.output_dir)
    return {
        "status": "completed",
        "logs": state.logs + ["Persisted migration summary JSON"],
    }
