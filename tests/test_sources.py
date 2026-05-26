import tempfile
import unittest
from pathlib import Path

from legal_rag.sources import load_jsonl_sources


class SourceLoaderTests(unittest.TestCase):
    def test_loads_jsonl_sources_into_documents(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sources.jsonl"
            path.write_text(
                '{"id":"judiciary-small-claims","title":"Small Claims Tribunals","source":"Singapore Judiciary","url":"https://www.judiciary.gov.sg/civil/small-claims","text":"Small Claims Tribunals hear certain low-value civil claims.","tags":["civil","small claims"]}\n',
                encoding="utf-8",
            )

            documents = load_jsonl_sources(path)

        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0].id, "judiciary-small-claims")
        self.assertEqual(documents[0].tags, ("civil", "small claims"))

    def test_rejects_non_official_source_url(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sources.jsonl"
            path.write_text(
                '{"id":"bad","title":"Blog","source":"Blog","url":"https://example.com/legal","text":"Unofficial commentary","tags":[]}\n',
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                load_jsonl_sources(path)


if __name__ == "__main__":
    unittest.main()
