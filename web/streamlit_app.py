from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from gh_ocr_paddle_agent.core.config import EVAL_DIR, RUNS_DIR
from gh_ocr_paddle_agent.core.evaluation import evaluate_fixtures
from gh_ocr_paddle_agent.graph.workflow import run_migration
from gh_ocr_paddle_agent.storage.runs import load_summaries


st.set_page_config(page_title="GitHubOCR -> PaddleOCR Agent", layout="wide")

st.title("GitHubOCR -> PaddleOCR Agent")
st.caption("LangGraph workflow for migrating OCR repositories to PaddleOCR-oriented projects.")

tab_migrate, tab_runs, tab_eval = st.tabs(["迁移仓库", "历史运行", "评测"])

with tab_migrate:
    source = st.text_input(
        "仓库地址或本地路径",
        value="",
        placeholder="https://github.com/example/ocr-project.git",
    )
    output_dir = st.text_input("输出目录（可选）", value="")

    if st.button("开始迁移", type="primary", disabled=not bool(source.strip())):
        with st.spinner("正在执行 LangGraph 工作流..."):
            state = run_migration(source.strip(), output_dir.strip() or None)
        st.success(f"迁移完成: {state.run_id}")
        if state.plan:
            st.subheader("检测结果")
            st.json(state.plan.model_dump())
        if state.verification:
            st.subheader("验证结果")
            st.json(state.verification.model_dump())
        report_path = Path(state.output_dir) / "migration_report.md"
        if report_path.exists():
            st.subheader("迁移报告")
            st.markdown(report_path.read_text(encoding="utf-8"))

with tab_runs:
    summaries = load_summaries(RUNS_DIR)
    if summaries:
        rows = [
            {
                "run_id": item["run_id"],
                "source": item["source"],
                "detected_stack": ", ".join(item["plan"]["source_stack"]),
                "verification_score": item["verification"]["score"],
                "output_dir": item["output_dir"],
            }
            for item in summaries
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
        selected = st.selectbox("查看某次运行详情", [item["run_id"] for item in summaries])
        selected_item = next(item for item in summaries if item["run_id"] == selected)
        st.json(selected_item)
    else:
        st.info("暂无历史运行。")

with tab_eval:
    if st.button("运行内置评测"):
        report_path = evaluate_fixtures()
        st.success(f"评测完成: {report_path}")

    latest_report = EVAL_DIR / "latest_eval_report.json"
    if latest_report.exists():
        report = json.loads(latest_report.read_text(encoding="utf-8"))
        st.subheader("评测总览")
        st.json(
            {
                "created_at": report["created_at"],
                "total_cases": report["total_cases"],
                "passed_cases": report["passed_cases"],
                "average_score": report["average_score"],
            }
        )
        st.subheader("用例详情")
        st.dataframe(pd.DataFrame(report["case_results"]), use_container_width=True)
    else:
        st.info("尚未生成评测报告。")

