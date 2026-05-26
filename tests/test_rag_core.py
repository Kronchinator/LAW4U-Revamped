import unittest

from legal_rag.core import LegalRAGAssistant, SourceDocument


class LegalRAGCoreTests(unittest.TestCase):
    def setUp(self):
        self.docs = [
            SourceDocument(
                id="penal-code-theft",
                title="Penal Code 1871 - Theft",
                source="Singapore Statutes Online",
                url="https://sso.agc.gov.sg/Act/PC1871",
                text="Whoever commits theft shall be punished under the Penal Code 1871. Theft involves dishonestly moving movable property out of any person's possession without consent.",
                tags=("criminal", "theft", "penal code"),
            ),
            SourceDocument(
                id="lab-legal-aid",
                title="Legal Aid Bureau - Applying for Legal Aid",
                source="Legal Aid Bureau",
                url="https://lab.mlaw.gov.sg/legal-services/apply-for-legal-aid/",
                text="The Legal Aid Bureau provides civil legal aid to eligible persons in Singapore subject to means and merits tests.",
                tags=("legal aid", "civil", "lab"),
            ),
        ]
        self.assistant = LegalRAGAssistant(self.docs, min_score=1)

    def test_retrieves_relevant_official_sources_for_singapore_legal_question(self):
        results = self.assistant.retrieve("What is theft under the Penal Code in Singapore?", limit=2)

        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0].document.id, "penal-code-theft")
        self.assertGreaterEqual(results[0].score, 2)

    def test_returns_no_source_result_when_question_is_not_grounded(self):
        result = self.assistant.prepare_answer("What is the best guitar for blues solos?")

        self.assertFalse(result.can_answer)
        self.assertEqual(result.sources, [])
        self.assertIn("Singapore legal sources", result.message)
        self.assertIn("qualified Singapore lawyer", result.message)

    def test_builds_grounded_messages_with_citations_and_disclaimer(self):
        result = self.assistant.prepare_answer("How do I apply for legal aid in Singapore?")

        self.assertTrue(result.can_answer)
        self.assertEqual(result.sources[0].document.id, "lab-legal-aid")
        joined = "\n".join(message["content"] for message in result.messages)
        self.assertIn("Legal Aid Bureau - Applying for Legal Aid", joined)
        self.assertIn("https://lab.mlaw.gov.sg/legal-services/apply-for-legal-aid/", joined)
        self.assertIn("not a substitute for professional legal counsel", joined)


if __name__ == "__main__":
    unittest.main()
