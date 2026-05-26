#!/usr/bin/env python3
"""Run the deterministic Stage 1 benchmark and write eval/report.md."""

from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    # Allows `python3 eval/run_eval.py` to work without installing the package.
    sys.path.insert(0, str(REPO_ROOT))

from chatbot import build_assistant
from legal_rag.evaluation import (
    evaluate_all,
    load_benchmark,
    render_markdown_report,
    summarise_results,
)

BENCHMARK_PATH = REPO_ROOT / "eval" / "benchmark_questions.jsonl"
REPORT_PATH = REPO_ROOT / "eval" / "report.md"


def main() -> int:
    assistant = build_assistant()
    questions = load_benchmark(BENCHMARK_PATH)
    results = evaluate_all(assistant, questions)
    summary = summarise_results(results)
    report = render_markdown_report(summary, results)

    REPORT_PATH.write_text(report, encoding="utf-8")

    print(report)
    return 0 if summary.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
