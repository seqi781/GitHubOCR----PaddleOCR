from pathlib import Path

from gh_ocr_paddle_agent.graph.workflow import run_migration


def test_workflow_handles_missing_source(tmp_path):
    state = run_migration(str(tmp_path / "missing-repo"), output_dir=str(tmp_path / "run"))
    assert state.status == "failed"
    assert state.error
    assert (Path(state.output_dir) / "migration_summary.json").exists()

