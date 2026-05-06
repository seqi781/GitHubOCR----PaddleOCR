# GitHubOCR -> PaddleOCR Agent

一个基于 `LangGraph` 的仓库迁移智能体：输入一个 GitHub OCR 项目仓库地址或本地目录，自动扫描项目中的 OCR 技术栈，生成迁移计划，并输出一套面向 `PaddleOCR` 的改写产物、验证报告与评测结果。

## 目标

- 扫描 GitHub 上已有 OCR 仓库
- 识别 `pytesseract`、`easyocr` 等常见 OCR 依赖
- 生成迁移计划和风险说明
- 输出 `PaddleOCR` 版改写项目骨架与建议补丁
- 提供一套可重复跑的评测系统
- 提供网页查看入口

## 架构

工作流使用 `LangGraph`，主流程如下：

1. `resolve_source`
2. `inventory_repository`
3. `detect_ocr_stack`
4. `draft_migration_plan`
5. `rewrite_repository`
6. `verify_output`
7. `persist_run`

## 本地目录

```text
gh_ocr_paddle_agent/
  core/          # 数据模型、配置、评测
  detectors/     # OCR 栈识别与仓库扫描
  generators/    # PaddleOCR 迁移产物生成
  graph/         # LangGraph 工作流
  storage/       # 运行结果落盘
web/
  streamlit_app.py
fixtures/
  repos/         # 评测样例仓库
  expectations/  # 评测期望
tests/
```

## 安装

建议使用 Python `3.11`。当前项目将 `PaddleOCR` 作为可选运行依赖；即使未安装 `paddleocr`，迁移工作流、评测系统和网页也能先跑起来。

使用 `uv` 初始化环境：

```bash
uv python install 3.11
uv venv --python 3.11
source .venv/bin/activate
uv sync --group dev
```

如果要在当前项目环境里真正运行 `PaddleOCR`：

```bash
uv sync --group dev --extra runtime
```

## 运行

命令行迁移一个仓库：

```bash
uv run gh-ocr-paddle-agent migrate \
  --source https://github.com/example/ocr-project.git \
  --output-dir ./outputs/runs
```

跑内置评测：

```bash
uv run gh-ocr-paddle-agent evaluate
```

启动网页：

```bash
uv run streamlit run web/streamlit_app.py
```

## 评测系统

评测围绕四个维度：

- OCR 技术栈识别准确性
- 迁移产物完整性
- 改写后依赖是否正确替换到 `PaddleOCR`
- 输出报告是否包含风险与下一步建议

内置样例包括：

- `case_pytesseract`
- `case_easyocr`

## 输出产物

每次运行会在 `outputs/runs/<run_id>/` 生成：

- `migration_report.md`
- `migration_summary.json`
- `rewritten_repo/`
- `patches/suggested_changes.diff`

## 网页查看

网页支持：

- 输入 GitHub 仓库地址或本地路径
- 查看 OCR 技术栈识别结果
- 查看迁移计划与风险
- 浏览输出的改写文件
- 查看内置评测排行榜与最近运行记录

## 说明

这个项目当前聚焦在 **Python OCR 仓库** 的自动迁移上。对于复杂的业务代码、深度定制训练代码或多语言项目，会优先生成结构化迁移建议和 PaddleOCR 适配骨架，而不是承诺对任意仓库做完全无损的自动重写。
