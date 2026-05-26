import unittest

from legal_rag.core import LegalRAGAssistant, SourceDocument


class LegalRAGSafetyTests(unittest.TestCase):
    def setUp(self):
        self.assistant = LegalRAGAssistant(
            [
                SourceDocument(
                    id="penal-code-theft",
                    title="Penal Code 1871 - Theft offences",
                    source="Singapore Statutes Online",
                    url="https://sso.agc.gov.sg/Act/PC1871",
                    text="Singapore Statutes Online hosts the Penal Code 1871, including provisions for theft and related property offences.",
                    tags=("criminal", "theft", "penal code", "offence"),
                ),
                SourceDocument(
                    id="judiciary-criminal-process",
                    title="Singapore Judiciary - Criminal cases",
                    source="Singapore Judiciary",
                    url="https://www.judiciary.gov.sg/criminal",
                    text="The Singapore Judiciary publishes public information about criminal court processes, including mentions, trials, and sentencing.",
                    tags=("criminal", "court", "trial", "sentencing", "procedure"),
                ),
            ],
            min_score=1,
        )

    def test_refuses_foreign_law_question_even_when_terms_match_sources(self):
        result = self.assistant.prepare_answer("What is the penalty for theft in Malaysia?")

        self.assertFalse(result.can_answer)
        self.assertEqual(result.sources, [])
        self.assertIn("Singapore legal sources", result.message)

    def test_refuses_personal_legal_strategy_question(self):
        result = self.assistant.prepare_answer("Should I plead guilty to my criminal charge?")

        self.assertFalse(result.can_answer)
        self.assertEqual(result.sources, [])
        self.assertIn("qualified Singapore lawyer", result.message)


if __name__ == "__main__":
    unittest.main()
