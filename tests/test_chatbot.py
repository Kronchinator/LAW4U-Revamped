import unittest

import chatbot
from legal_rag.core import LegalRAGAssistant, SourceDocument


class FakeCompletions:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)

        class Message:
            content = "Grounded answer with citation."

        class Choice:
            message = Message()

        class Response:
            choices = [Choice()]

        return Response()


class FakeClient:
    def __init__(self):
        self.chat = type("Chat", (), {"completions": FakeCompletions()})()


class ChatbotQueryTests(unittest.TestCase):
    def setUp(self):
        self.assistant = LegalRAGAssistant(
            [
                SourceDocument(
                    id="lab",
                    title="Legal Aid Bureau",
                    source="Legal Aid Bureau",
                    url="https://lab.mlaw.gov.sg/legal-services/apply-for-legal-aid/",
                    text="Civil legal aid may be available subject to means and merits tests.",
                    tags=("legal aid", "civil"),
                )
            ],
            min_score=1,
        )

    def test_query_openai_returns_rag_refusal_without_model_call(self):
        client = FakeClient()

        answer = chatbot.query_openai("Recommend a guitar", client, self.assistant)

        self.assertIn("Singapore legal sources", answer)
        self.assertEqual(client.chat.completions.calls, [])

    def test_query_openai_sends_grounded_rag_messages_to_model(self):
        client = FakeClient()

        answer = chatbot.query_openai("How do I apply for legal aid?", client, self.assistant)

        self.assertEqual(answer, "Grounded answer with citation.")
        self.assertEqual(len(client.chat.completions.calls), 1)
        call = client.chat.completions.calls[0]
        self.assertEqual(call["model"], "gpt-4o-mini")
        self.assertIn("Official-source context", call["messages"][1]["content"])


if __name__ == "__main__":
    unittest.main()
