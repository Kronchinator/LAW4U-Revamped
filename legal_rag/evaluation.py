"""Deterministic evaluation helpers for the LegalCodebreaker RAG layer.

Stage 1 deliberately evaluates the retrieval/preparation layer without calling an
LLM. That keeps the benchmark cheap, repeatable, and focused on the behaviour we
control directly: retrieve official sources, refuse ungrounded prompts, and build
citation-ready messages.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from html import escape
import json
from pathlib import Path
from urllib.parse import urlparse

from .core import DISCLAIMER, LegalRAGAssistant, PreparedAnswer, RetrievalResult

ANSWER = "answer"
REFUSE = "refuse"


@dataclass(frozen=True)
class BenchmarkQuestion:
    """One benchmark item for the deterministic evaluation harness."""

    id: str
    question: str
    category: str
    expected_behavior: str
    expected_source_domains: tuple[str, ...]
    expected_keywords: tuple[str, ...]
    notes: str = ""
    risk_type: str = "general"


@dataclass(frozen=True)
class EvaluationResult:
    """Pass/fail details for one benchmark question."""

    id: str
    question: str
    category: str
    expected_behavior: str
    actual_can_answer: bool
    passed: bool
    behavior_passed: bool
    retrieval_passed: bool
    citation_passed: bool
    disclaimer_passed: bool
    keyword_passed: bool
    retrieved_sources: tuple[str, ...]
    notes: tuple[str, ...]
    risk_type: str


@dataclass(frozen=True)
class EvaluationSummary:
    """Aggregate metrics for a benchmark run."""

    total: int
    passed: int
    failed: int
    overall_pass_rate: float
    answerable_count: int
    refusal_count: int
    retrieval_accuracy: float
    refusal_accuracy: float
    citation_compliance: float
    disclaimer_compliance: float
    keyword_compliance: float


def load_benchmark(path: str | Path) -> list[BenchmarkQuestion]:
    """Load newline-delimited benchmark questions from JSONL."""

    benchmark_path = Path(path)
    questions: list[BenchmarkQuestion] = []
    with benchmark_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            raw = json.loads(line)
            expected_behavior = str(raw["expected_behavior"])
            if expected_behavior not in {ANSWER, REFUSE}:
                raise ValueError(
                    f"Line {line_number}: expected_behavior must be 'answer' or 'refuse'"
                )
            questions.append(
                BenchmarkQuestion(
                    id=str(raw["id"]),
                    question=str(raw["question"]),
                    category=str(raw["category"]),
                    expected_behavior=expected_behavior,
                    expected_source_domains=tuple(raw.get("expected_source_domains", ())),
                    expected_keywords=tuple(raw.get("expected_keywords", ())),
                    notes=str(raw.get("notes", "")),
                    risk_type=str(raw.get("risk_type", "general")),
                )
            )
    return questions


def evaluate_all(
    assistant: LegalRAGAssistant, questions: list[BenchmarkQuestion]
) -> list[EvaluationResult]:
    """Evaluate every benchmark question with the same assistant instance."""

    return [evaluate_question(assistant, question) for question in questions]


def evaluate_question(
    assistant: LegalRAGAssistant, question: BenchmarkQuestion
) -> EvaluationResult:
    """Evaluate one question against retrieval, citation, refusal, and disclaimer checks."""

    prepared = assistant.prepare_answer(question.question)
    notes: list[str] = []

    behavior_passed = _check_behavior(prepared, question)
    if not behavior_passed:
        notes.append(
            f"Expected {question.expected_behavior}, got {'answer' if prepared.can_answer else 'refuse'}."
        )

    if question.expected_behavior == REFUSE:
        retrieval_passed = True
        citation_passed = True
        disclaimer_passed = True
        keyword_passed = True
    else:
        retrieval_passed = _check_retrieval(prepared.sources, question.expected_source_domains)
        citation_passed = _check_citations(prepared, question.expected_source_domains)
        disclaimer_passed = _message_text(prepared).find(DISCLAIMER) != -1
        keyword_passed = _check_keywords(prepared, question.expected_keywords)
        if not retrieval_passed:
            notes.append("No retrieved source matched the expected domain list.")
        if not citation_passed:
            notes.append("The prepared prompt did not include an expected source URL.")
        if not disclaimer_passed:
            notes.append("The prepared prompt did not include the legal disclaimer.")
        if not keyword_passed:
            notes.append("The prepared prompt missed one or more expected keywords.")

    passed = all(
        [
            behavior_passed,
            retrieval_passed,
            citation_passed,
            disclaimer_passed,
            keyword_passed,
        ]
    )

    return EvaluationResult(
        id=question.id,
        question=question.question,
        category=question.category,
        expected_behavior=question.expected_behavior,
        actual_can_answer=prepared.can_answer,
        passed=passed,
        behavior_passed=behavior_passed,
        retrieval_passed=retrieval_passed,
        citation_passed=citation_passed,
        disclaimer_passed=disclaimer_passed,
        keyword_passed=keyword_passed,
        retrieved_sources=tuple(result.document.url for result in prepared.sources),
        notes=tuple(notes),
        risk_type=question.risk_type,
    )


def summarise_results(results: list[EvaluationResult]) -> EvaluationSummary:
    """Calculate percentage metrics for an evaluation run."""

    total = len(results)
    passed = sum(result.passed for result in results)
    answerable = [result for result in results if result.expected_behavior == ANSWER]
    refusals = [result for result in results if result.expected_behavior == REFUSE]

    return EvaluationSummary(
        total=total,
        passed=passed,
        failed=total - passed,
        overall_pass_rate=_percent(passed, total),
        answerable_count=len(answerable),
        refusal_count=len(refusals),
        retrieval_accuracy=_percent(sum(result.retrieval_passed for result in answerable), len(answerable)),
        refusal_accuracy=_percent(sum(result.behavior_passed for result in refusals), len(refusals)),
        citation_compliance=_percent(sum(result.citation_passed for result in answerable), len(answerable)),
        disclaimer_compliance=_percent(sum(result.disclaimer_passed for result in answerable), len(answerable)),
        keyword_compliance=_percent(sum(result.keyword_passed for result in answerable), len(answerable)),
    )


def render_markdown_report(
    summary: EvaluationSummary,
    results: list[EvaluationResult],
    generated_at: datetime | None = None,
) -> str:
    """Render a small report that can be committed with the benchmark."""

    timestamp = (generated_at or datetime.now(UTC)).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# LegalCodebreaker evaluation report",
        "",
        f"Generated: {timestamp}",
        "",
        "## Summary",
        "",
        f"- Total benchmark questions: {summary.total}",
        f"- Passed: {summary.passed}",
        f"- Failed: {summary.failed}",
        f"- Overall pass rate: {summary.overall_pass_rate:.1f}%",
        f"- Retrieval accuracy: {summary.retrieval_accuracy:.1f}%",
        f"- Refusal accuracy: {summary.refusal_accuracy:.1f}%",
        f"- Citation compliance: {summary.citation_compliance:.1f}%",
        f"- Disclaimer compliance: {summary.disclaimer_compliance:.1f}%",
        f"- Keyword compliance: {summary.keyword_compliance:.1f}%",
        "",
        "## What this measures",
        "",
        "This Stage 1 benchmark checks the deterministic RAG layer. It does not call the language model. It checks whether the system retrieves expected official-source domains, refuses questions it should not answer, and builds prompts with citations and the legal disclaimer.",
        "",
        "## Results by question",
        "",
    ]

    for result in results:
        status = "PASS" if result.passed else "FAIL"
        lines.extend(
            [
                f"### {result.id}: {status}",
                "",
                f"- Category: {result.category}",
                f"- Risk type: {result.risk_type}",
                f"- Expected behaviour: {result.expected_behavior}",
                f"- Actual behaviour: {'answer' if result.actual_can_answer else 'refuse'}",
                f"- Retrieved sources: {', '.join(result.retrieved_sources) if result.retrieved_sources else 'None'}",
                f"- Notes: {'; '.join(result.notes) if result.notes else 'None'}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_html_dashboard(
    summary: EvaluationSummary,
    results: list[EvaluationResult],
    generated_at: datetime | None = None,
) -> str:
    """Render a self-contained AI Trust Lab dashboard for GitHub/demo review."""

    timestamp = (generated_at or datetime.now(UTC)).strftime("%Y-%m-%d %H:%M UTC")
    categories = _category_breakdown(results)
    cards = [
        ("Total questions", str(summary.total)),
        ("Passed", str(summary.passed)),
        ("Failed", str(summary.failed)),
        ("Overall pass rate", f"{summary.overall_pass_rate:.1f}%"),
        ("Retrieval accuracy", f"{summary.retrieval_accuracy:.1f}%"),
        ("Refusal accuracy", f"{summary.refusal_accuracy:.1f}%"),
        ("Citation compliance", f"{summary.citation_compliance:.1f}%"),
        ("Disclaimer compliance", f"{summary.disclaimer_compliance:.1f}%"),
    ]

    card_html = "\n".join(
        f"""
        <section class="metric-card">
          <span>{escape(label)}</span>
          <strong>{escape(value)}</strong>
        </section>"""
        for label, value in cards
    )
    category_rows = "\n".join(
        f"""
        <tr>
          <td>{escape(category)}</td>
          <td>{counts['passed']} / {counts['total']}</td>
          <td>{_percent(counts['passed'], counts['total']):.1f}%</td>
        </tr>"""
        for category, counts in sorted(categories.items())
    )
    result_rows = "\n".join(
        f"""
        <article class="result {'pass' if result.passed else 'fail'}">
          <div class="result-head">
            <strong>{escape(result.id)}</strong>
            <span>{'PASS' if result.passed else 'FAIL'}</span>
          </div>
          <p>{escape(result.question)}</p>
          <dl>
            <dt>Category</dt><dd>{escape(result.category)}</dd>
            <dt>Risk type</dt><dd>{escape(result.risk_type)}</dd>
            <dt>Expected</dt><dd>{escape(result.expected_behavior)}</dd>
            <dt>Actual</dt><dd>{'answer' if result.actual_can_answer else 'refuse'}</dd>
            <dt>Sources</dt><dd>{escape(', '.join(result.retrieved_sources) if result.retrieved_sources else 'None')}</dd>
          </dl>
        </article>"""
        for result in results
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AI Trust Lab - LegalCodebreaker evaluation</title>
  <style>
    body {{ margin: 0; font-family: Inter, system-ui, sans-serif; background: #111827; color: #e5e7eb; }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 40px 20px; }}
    header {{ margin-bottom: 28px; }}
    h1 {{ margin: 0 0 8px; font-size: clamp(2rem, 5vw, 4rem); }}
    .subtitle {{ max-width: 760px; color: #cbd5e1; line-height: 1.6; }}
    .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 14px; margin: 28px 0; }}
    .metric-card {{ background: #1f2937; border: 1px solid #334155; border-radius: 16px; padding: 18px; }}
    .metric-card span {{ display: block; color: #94a3b8; font-size: .9rem; margin-bottom: 8px; }}
    .metric-card strong {{ font-size: 1.8rem; }}
    table {{ width: 100%; border-collapse: collapse; background: #1f2937; border-radius: 16px; overflow: hidden; }}
    th, td {{ text-align: left; padding: 12px 14px; border-bottom: 1px solid #334155; }}
    th {{ color: #93c5fd; }}
    .results {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(310px, 1fr)); gap: 14px; margin-top: 18px; }}
    .result {{ background: #1f2937; border-radius: 16px; padding: 16px; border: 1px solid #334155; }}
    .result.pass {{ border-color: #059669; }}
    .result.fail {{ border-color: #dc2626; }}
    .result-head {{ display: flex; justify-content: space-between; gap: 12px; }}
    .result-head span {{ color: #a7f3d0; font-weight: 700; }}
    .result.fail .result-head span {{ color: #fecaca; }}
    dl {{ display: grid; grid-template-columns: 90px 1fr; gap: 6px 12px; color: #cbd5e1; }}
    dt {{ color: #94a3b8; }}
    footer {{ color: #94a3b8; margin-top: 32px; }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>AI Trust Lab</h1>
      <p class="subtitle">A deterministic evaluation dashboard for LegalCodebreaker. It checks the part of the system I control directly: whether the assistant retrieves official Singapore sources, refuses unsafe or unsupported questions, and prepares citation-ready prompts before any model call.</p>
      <p>Generated: {escape(timestamp)}</p>
    </header>
    <section class="metrics">{card_html}</section>
    <h2>Category breakdown</h2>
    <table>
      <thead><tr><th>Category</th><th>Passed</th><th>Pass rate</th></tr></thead>
      <tbody>{category_rows}</tbody>
    </table>
    <h2>Question results</h2>
    <section class="results">{result_rows}</section>
    <footer>This dashboard does not prove legal correctness. It proves that the retrieval and refusal layer can be tested instead of trusted on vibes.</footer>
  </main>
</body>
</html>
"""


def _category_breakdown(results: list[EvaluationResult]) -> dict[str, dict[str, int]]:
    categories: dict[str, dict[str, int]] = {}
    for result in results:
        bucket = categories.setdefault(result.category, {"total": 0, "passed": 0})
        bucket["total"] += 1
        bucket["passed"] += int(result.passed)
    return categories


def _check_behavior(prepared: PreparedAnswer, question: BenchmarkQuestion) -> bool:
    if question.expected_behavior == ANSWER:
        return prepared.can_answer
    return not prepared.can_answer


def _check_retrieval(
    sources: list[RetrievalResult], expected_domains: tuple[str, ...]
) -> bool:
    if not expected_domains:
        return True
    if not sources:
        return False

    # Stage 1 is intentionally strict: the expected domain must be the top hit,
    # not merely somewhere in a long context window.
    return _domain(sources[0].document.url) in set(expected_domains)


def _check_citations(prepared: PreparedAnswer, expected_domains: tuple[str, ...]) -> bool:
    if not expected_domains:
        return True
    text = _message_text(prepared)
    return any(domain in text for domain in expected_domains)


def _check_keywords(prepared: PreparedAnswer, expected_keywords: tuple[str, ...]) -> bool:
    text = _message_text(prepared).lower()
    return all(keyword.lower() in text for keyword in expected_keywords)


def _message_text(prepared: PreparedAnswer) -> str:
    return "\n".join(message["content"] for message in prepared.messages)


def _domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def _percent(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 100.0
    return round((numerator / denominator) * 100, 1)

