from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from gh_ocr_paddle_agent.core.config import EVAL_DIR, RUNS_DIR
from gh_ocr_paddle_agent.core.evaluation import evaluate_fixtures
from gh_ocr_paddle_agent.core.inspect import list_text_files, read_text_excerpt
from gh_ocr_paddle_agent.graph.workflow import run_migration
from gh_ocr_paddle_agent.storage.runs import load_summaries


st.set_page_config(page_title="GitHubOCR -> PaddleOCR Agent", layout="wide")

st.title("GitHubOCR -> PaddleOCR Agent")
st.caption("LangGraph workflow for migrating OCR repositories to PaddleOCR-oriented projects.")

tab_migrate, tab_runs, tab_eval = st.tabs(["迁移仓库", "历史运行", "评测"])

with tab_migrate:
    use_fixture = st.checkbox("使用内置样例仓库", value=False)
    default_source = "fixtures/repos/case_pytesseract" if use_fixture else ""
    source = st.text_input(
        "仓库地址或本地路径",
        value=default_source,
        placeholder="https://github.com/example/ocr-project.git",
    )
    output_dir = st.text_input("输出目录（可选）", value="")

    if st.button("开始迁移", type="primary", disabled=not bool(source.strip())):
        with st.spinner("正在执行 LangGraph 工作流..."):
            state = run_migration(source.strip(), output_dir.strip() or None)
        if state.status == "failed":
            st.error(f"迁移失败: {state.error}")
        else:
            st.success(f"迁移完成: {state.run_id}")

        cols = st.columns(4)
        cols[0].metric("状态", state.status)
        cols[1].metric("识别栈数", len(state.plan.source_stack) if state.plan else 0)
        cols[2].metric("验证分数", state.verification.score if state.verification else 0.0)
        cols[3].metric("产物数", len(state.artifacts))

        if state.plan:
            st.subheader("检测结果")
            st.json(state.plan.model_dump())
        if state.repository:
            st.subheader("仓库画像")
            st.json(state.repository.model_dump())
        if state.verification:
            st.subheader("验证结果")
            st.json(state.verification.model_dump())
        if state.logs:
            st.subheader("运行日志")
            st.code("\n".join(state.logs), language="text")
        report_path = Path(state.output_dir) / "migration_report.md"
        if report_path.exists():
            st.subheader("迁移报告")
            st.markdown(report_path.read_text(encoding="utf-8"))
        rewritten_root = Path(state.output_dir) / "rewritten_repo"
        files = list_text_files(rewritten_root)
        if files:
            st.subheader("改写后文件预览")
            selected = st.selectbox(
                "选择文件",
                [str(path.relative_to(rewritten_root)) for path in files],
                key=f"preview-{state.run_id}",
            )
            selected_path = rewritten_root / selected
            st.code(read_text_excerpt(selected_path), language="python")

with tab_runs:
    summaries = load_summaries(RUNS_DIR)
    if summaries:
        rows = [
            {
                "run_id": item["run_id"],
                "source": item["source"],
                "status": item.get("status", "completed" if item.get("verification") else "failed"),
                "detected_stack": ", ".join(item.get("plan", {}).get("source_stack", [])),
                "verification_score": item.get("verification", {}).get("score", 0.0),
                "output_dir": item["output_dir"],
            }
            for item in summaries
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
        selected = st.selectbox("查看某次运行详情", [item["run_id"] for item in summaries])
        selected_item = next(item for item in summaries if item["run_id"] == selected)
        st.json(selected_item)
        run_root = Path(selected_item["output_dir"])
        rewritten_root = run_root / "rewritten_repo"
        files = list_text_files(rewritten_root)
        if files:
            selected_file = st.selectbox(
                "浏览产物文件",
                [str(path.relative_to(rewritten_root)) for path in files],
                key=f"run-file-{selected}",
            )
            st.code(read_text_excerpt(rewritten_root / selected_file), language="python")
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
        cols = st.columns(4)
        cols[0].metric("生成时间", report["created_at"])
        cols[1].metric("总用例", report["total_cases"])
        cols[2].metric("通过数", report["passed_cases"])
        cols[3].metric("平均分", report["average_score"])
        st.subheader("用例详情")
        st.dataframe(pd.DataFrame(report["case_results"]), use_container_width=True)
    else:
        st.info("尚未生成评测报告。")
