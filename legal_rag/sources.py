"""Load and validate source documents for the LegalCodebreaker RAG index."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

from .core import SourceDocument

OFFICIAL_DOMAINS = {
    "sso.agc.gov.sg",
    "agc.gov.sg",
    "www.agc.gov.sg",
    "judiciary.gov.sg",
    "www.judiciary.gov.sg",
    "mlaw.gov.sg",
    "www.mlaw.gov.sg",
    "lab.mlaw.gov.sg",
}


def load_jsonl_sources(path: str | Path) -> list[SourceDocument]:
    """Load JSONL source records, rejecting non-official Singapore legal URLs."""

    source_path = Path(path)
    documents: list[SourceDocument] = []

    with source_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            raw = json.loads(line)
            url = str(raw["url"])
            domain = urlparse(url).netloc.lower()
            if domain not in OFFICIAL_DOMAINS:
                raise ValueError(
                    f"Line {line_number}: source URL must be from an approved official domain, got {domain!r}"
                )
            documents.append(
                SourceDocument(
                    id=str(raw["id"]),
                    title=str(raw["title"]),
                    source=str(raw["source"]),
                    url=url,
                    text=str(raw["text"]),
                    tags=tuple(str(tag) for tag in raw.get("tags", ())),
                )
            )

    return documents
