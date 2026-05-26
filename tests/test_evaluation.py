import tempfile
import unittest
from pathlib import Path

from legal_rag.core import LegalRAGAssistant, SourceDocument
from legal_rag.evaluation import (
    BenchmarkQuestion,
    evaluate_all,
    evaluate_question,
    load_benchmark,
    render_markdown_report,
    summarise_results,
)


class EvaluationHarnessTests(unittest.TestCase):
    def setUp(self):
        self.assistant = LegalRAGAssistant(
            [
                SourceDocument(
                    id="lab-legal-aid",
                    title="Legal Aid Bureau - Applying for legal aid",
                    source="Legal Aid Bureau",
                    url="https://lab.mlaw.gov.sg/legal-services/apply-for-legal-aid/",
                    text="The Legal Aid Bureau provides civil legal aid subject to means and merits tests.",
                    tags=("legal aid", "civil", "lawyer"),
                ),
                SourceDocument(
                    id="judiciary-small-claims",
                    title="Singapore Judiciary - Small Claims Tribunals",
                    source="Singapore Judiciary",
                    url="https://www.judiciary.gov.sg/civil/small-claims",
                    text="Small Claims Tribunals hear certain low-value civil claims in Singapore.",
                    tags=("civil", "small claims", "tribunal"),
                ),
            ],
            min_score=1,
        )

    def test_load_benchmark_reads_jsonl_questions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "benchmark.jsonl"
            path.write_text(
                '{"id":"lab_001","question":"How do I apply for legal aid?","category":"legal_aid","expected_behavior":"answer","expected_source_domains":["lab.mlaw.gov.sg"],"expected_keywords":["means","merits"],"notes":"LAB question"}\n',
                encoding="utf-8",
            )

            questions = load_benchmark(path)

        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0].id, "lab_001")
        self.assertEqual(questions[0].expected_source_domains, ("lab.mlaw.gov.sg",))

    def test_evaluate_question_passes_answerable_source_grounded_question(self):
        question = BenchmarkQuestion(
            id="lab_001",
            question="How do I apply for legal aid in Singapore?",
            category="legal_aid",
            expected_behavior="answer",
            expected_source_domains=("lab.mlaw.gov.sg",),
            expected_keywords=("means", "merits"),
            notes="Should retrieve LAB legal aid source.",
        )

        result = evaluate_question(self.assistant, question)

        self.assertTrue(result.passed, result.notes)
        self.assertTrue(result.behavior_passed)
        self.assertTrue(result.retrieval_passed)
        self.assertTrue(result.citation_passed)
        self.assertTrue(result.disclaimer_passed)
        self.assertTrue(result.keyword_passed)

    def test_evaluate_question_passes_refusal_question(self):
        question = BenchmarkQuestion(
            id="offtopic_001",
            question="What electric guitar should I buy for blues?",
            category="off_topic",
            expected_behavior="refuse",
            expected_source_domains=(),
            expected_keywords=(),
            notes="Should refuse unrelated questions.",
        )

        result = evaluate_question(self.assistant, question)

        self.assertTrue(result.passed, result.notes)
        self.assertTrue(result.behavior_passed)
        self.assertFalse(result.actual_can_answer)

    def test_summarise_results_computes_rates(self):
        questions = [
            BenchmarkQuestion(
                id="lab_001",
                question="How do I apply for legal aid in Singapore?",
                category="legal_aid",
                expected_behavior="answer",
                expected_source_domains=("lab.mlaw.gov.sg",),
                expected_keywords=("means", "merits"),
                notes="",
            ),
            BenchmarkQuestion(
                id="offtopic_001",
                question="What electric guitar should I buy for blues?",
                category="off_topic",
                expected_behavior="refuse",
                expected_source_domains=(),
                expected_keywords=(),
                notes="",
            ),
        ]

        summary = summarise_results(evaluate_all(self.assistant, questions))

        self.assertEqual(summary.total, 2)
        self.assertEqual(summary.passed, 2)
        self.assertEqual(summary.overall_pass_rate, 100.0)
        self.assertEqual(summary.refusal_accuracy, 100.0)
        self.assertEqual(summary.retrieval_accuracy, 100.0)

    def test_render_markdown_report_includes_metrics_and_failures(self):
        questions = [
            BenchmarkQuestion(
                id="lab_001",
                question="How do I apply for legal aid in Singapore?",
                category="legal_aid",
                expected_behavior="answer",
                expected_source_domains=("lab.mlaw.gov.sg",),
                expected_keywords=("means", "merits"),
                notes="",
            )
        ]
        results = evaluate_all(self.assistant, questions)

        report = render_markdown_report(summarise_results(results), results)

        self.assertIn("# LegalCodebreaker evaluation report", report)
        self.assertIn("Overall pass rate: 100.0%", report)
        self.assertIn("lab_001", report)


if __name__ == "__main__":
    unittest.main()
