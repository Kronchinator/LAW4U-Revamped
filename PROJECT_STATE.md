# singapore-legal-bot

Singapore Legal RAG Assistant / Telegram bot.

## Current state

Refactored from a direct OpenAI prompt skeleton into a testable RAG MVP with a Stage 1 evaluation harness:

- `legal_rag/core.py` contains retrieval, grounding, prompt construction, citation-context formatting, refusal behaviour, and basic safety gates for foreign-law and personal legal-strategy questions.
- `legal_rag/sources.py` loads JSONL source chunks and rejects non-official domains.
- `legal_rag/evaluation.py` scores deterministic RAG behaviour without calling an LLM.
- `data/official_sources.jsonl` contains a small seed set of official Singapore legal/public-source records.
- `eval/benchmark_questions.jsonl` contains 20 benchmark questions covering answerable Singapore legal-access questions, off-topic prompts, foreign-law prompts, and personal legal-advice prompts.
- `eval/run_eval.py` runs the benchmark and writes `eval/report.md`.
- `chatbot.py` uses environment variables instead of hardcoded placeholders and refuses ungrounded questions before calling OpenAI.
- `tests/` covers retrieval, source validation, refusal behaviour, OpenAI call behaviour, safety boundaries, and evaluation metrics.

## Verification

Run from repo root:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 eval/run_eval.py
python3 -m py_compile chatbot.py legal_rag/*.py eval/run_eval.py
```

Latest local verification:

- Unit tests: 14 passed
- Stage 1 evaluation: 20 / 20 benchmark questions passed

## Next priority

Build the stronger admissions evidence layer:

1. Expand official source chunks from SSO, Judiciary, MinLaw, AGC, and LAB.
2. Increase the benchmark from 20 to 50 questions.
3. Add optional model-output evaluation for final answer citations and unsupported claims.
4. Add screenshots or a demo transcript for the README.

Original source path: `/home/openclaw/.openclaw/workspace/main/singapore-legal-bot`

Secrets, runtime state, dependency folders, logs, and generated build artifacts were intentionally excluded from this staged copy.
