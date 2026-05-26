"""Deterministic evaluation helpers for the LegalCodebreaker RAG layer.

Stage 1 deliberately evaluates the retrieval/preparation layer without calling an
LLM. That keeps the benchmark cheap, repeatable, and focused on the behaviour we
control directly: retrieve official sources, refuse ungrounded prompts, and build
citation-ready messages.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
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
                f"- Expected behaviour: {result.expected_behavior}",
                f"- Actual behaviour: {'answer' if result.actual_can_answer else 'refuse'}",
                f"- Retrieved sources: {', '.join(result.retrieved_sources) if result.retrieved_sources else 'None'}",
                f"- Notes: {'; '.join(result.notes) if result.notes else 'None'}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


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
