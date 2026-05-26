# singapore-legal-bot

Singapore Legal RAG Assistant / Telegram bot.

## Current state

Refactored from a direct OpenAI prompt skeleton into a testable RAG MVP:

- `legal_rag/core.py` contains retrieval, grounding, prompt construction, citation-context formatting, and refusal behaviour.
- `legal_rag/sources.py` loads JSONL source chunks and rejects non-official domains.
- `data/official_sources.jsonl` contains a small seed set of official Singapore legal/public-source records.
- `chatbot.py` now uses environment variables instead of hardcoded placeholders and refuses ungrounded questions before calling OpenAI.
- `tests/` covers retrieval, source validation, refusal behaviour, and OpenAI call behaviour.

## Verification

Run from repo root:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 -m py_compile chatbot.py legal_rag/*.py
```

## Next priority

Build the admissions-worthy evidence layer:

1. Add 30-50 benchmark questions.
2. Expand official source chunks from SSO, Judiciary, MinLaw, AGC, and LAB.
3. Add evaluation metrics for citation accuracy, refusal accuracy, and hallucination rate.
4. Add screenshots/demo transcript for the README.

Original source path: `/home/openclaw/.openclaw/workspace/main/singapore-legal-bot`

Secrets, runtime state, dependency folders, logs, and generated build artifacts were intentionally excluded from this staged copy.
