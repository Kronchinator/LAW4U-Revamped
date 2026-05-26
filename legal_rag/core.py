"""Core retrieval and grounding logic for LegalCodebreaker.

This module is deliberately dependency-light so the admissions portfolio can show
clear RAG mechanics before any vector database or paid API is added.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Sequence


DISCLAIMER = (
    "This is general information only and is not a substitute for professional "
    "legal counsel. For serious matters, consult a qualified Singapore lawyer."
)

SYSTEM_PROMPT = """You are LegalCodebreaker, a Singapore legal information assistant.

Rules:
1. Answer only using the official-source context provided by the retrieval layer.
2. If the context does not contain enough information, say that the answer cannot be grounded in the provided Singapore legal sources.
3. Cite every legal claim with the source title and URL supplied in the context.
4. Do not give personal legal advice, strategy, or predictions about a user's case.
5. End every answer with this disclaimer: This is general information only and is not a substitute for professional legal counsel. For serious matters, consult a qualified Singapore lawyer.
"""

LEGAL_TERMS = {
    "act",
    "appeal",
    "bail",
    "case",
    "civil",
    "claim",
    "contract",
    "court",
    "criminal",
    "divorce",
    "employment",
    "jail",
    "judge",
    "judiciary",
    "law",
    "lawsuit",
    "legal",
    "offence",
    "penal",
    "police",
    "procedure",
    "sentence",
    "singapore",
    "statute",
    "sue",
    "theft",
    "trial",
}

FOREIGN_JURISDICTION_TERMS = {
    "australia",
    "canada",
    "china",
    "india",
    "indonesia",
    "japan",
    "malaysia",
    "philippines",
    "thailand",
    "uk",
    "united kingdom",
    "us",
    "usa",
    "vietnam",
}

PERSONAL_ADVICE_PATTERNS = (
    "should i",
    "can i win",
    "will i win",
    "what should i do",
    "help me win",
    "my case",
    "my charge",
    "plead guilty",
)

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "under",
    "what",
    "when",
    "where",
    "who",
    "why",
}


@dataclass(frozen=True)
class SourceDocument:
    """A chunk of official Singapore legal material available for retrieval."""

    id: str
    title: str
    source: str
    url: str
    text: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class RetrievalResult:
    """A retrieved source plus the simple lexical score that ranked it."""

    document: SourceDocument
    score: int
    matched_terms: tuple[str, ...]


@dataclass(frozen=True)
class PreparedAnswer:
    """RAG preparation result returned before any LLM call is made."""

    can_answer: bool
    message: str
    sources: list[RetrievalResult]
    messages: list[dict[str, str]]


def tokenize(text: str) -> set[str]:
    """Normalize text into searchable terms."""

    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 1 and token not in STOPWORDS
    }


class LegalRAGAssistant:
    """Small, testable RAG core: retrieve official sources then build prompts."""

    def __init__(self, documents: Iterable[SourceDocument], min_score: int = 2):
        self.documents = list(documents)
        self.min_score = min_score

    def retrieve(self, query: str, limit: int = 4) -> list[RetrievalResult]:
        query_terms = tokenize(query)
        if not query_terms:
            return []

        results: list[RetrievalResult] = []
        for document in self.documents:
            document_terms = tokenize(
                " ".join([document.title, document.source, document.text, *document.tags])
            )
            matched_terms = tuple(sorted(query_terms & document_terms))
            if not matched_terms:
                continue

            tag_terms = tokenize(" ".join(document.tags))
            title_terms = tokenize(document.title)
            score = len(matched_terms)
            score += len(query_terms & tag_terms)
            score += len(query_terms & title_terms)

            results.append(
                RetrievalResult(
                    document=document,
                    score=score,
                    matched_terms=matched_terms,
                )
            )

        results.sort(key=lambda result: (-result.score, result.document.title))
        return results[:limit]

    def prepare_answer(self, query: str, limit: int = 4) -> PreparedAnswer:
        sources = [
            result
            for result in self.retrieve(query, limit=limit)
            if result.score >= self.min_score
        ]

        if not self._looks_like_singapore_legal_question(query) or not sources:
            message = (
                "I cannot ground this in the available Singapore legal sources. "
                "Please ask a Singapore law, court procedure, or legal-aid question, "
                "or consult a qualified Singapore lawyer for advice."
            )
            return PreparedAnswer(
                can_answer=False,
                message=message,
                sources=[],
                messages=[],
            )

        context = self._format_context(sources)
        user_prompt = (
            f"User question:\n{query}\n\n"
            f"Official-source context:\n{context}\n\n"
            "Answer clearly in plain English. Use numbered points if helpful. "
            "Cite source titles and URLs for claims. "
            f"End with: {DISCLAIMER}"
        )
        return PreparedAnswer(
            can_answer=True,
            message="",
            sources=sources,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )

    def _looks_like_singapore_legal_question(self, query: str) -> bool:
        terms = tokenize(query)
        normalized_query = query.lower()

        # The bot is intentionally Singapore-only. Without this gate, a foreign-law
        # question about "theft" could match the Penal Code source and look grounded.
        if terms & FOREIGN_JURISDICTION_TERMS:
            return False
        if any(pattern in normalized_query for pattern in PERSONAL_ADVICE_PATTERNS):
            return False

        return bool(terms & LEGAL_TERMS)

    def _format_context(self, sources: Sequence[RetrievalResult]) -> str:
        sections = []
        for index, result in enumerate(sources, start=1):
            document = result.document
            sections.append(
                "\n".join(
                    [
                        f"[{index}] {document.title}",
                        f"Source: {document.source}",
                        f"URL: {document.url}",
                        f"Matched terms: {', '.join(result.matched_terms)}",
                        f"Extract: {document.text}",
                    ]
                )
            )
        return "\n\n".join(sections)
