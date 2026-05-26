# LegalCodebreaker: Singapore legal RAG assistant

LegalCodebreaker answers Singapore legal information questions using retrieved official sources before it calls an LLM.

The first version of this repo was a simple Telegram bot with a long system prompt. This version moves the important parts into a small RAG core: source validation, retrieval, prompt building, citations, refusal behaviour, and now a deterministic evaluation harness.

Current status: working MVP foundation. It is not a full legal database yet.

## Why I built it this way

Legal chatbots can be risky. If a model guesses, the answer may sound confident and still be wrong.

So the rule here is simple:

**No official Singapore source retrieved → no model answer.**

That keeps the bot honest. It also makes the project more than a Telegram wrapper around OpenAI. The useful part is the guardrail: validate the sources, retrieve the relevant context, refuse when the question falls outside the available evidence, then measure whether those behaviours actually work.

## What is RAG?

RAG means retrieval-augmented generation. The model does not answer from memory alone. The system first retrieves relevant source material, then gives that material to the model as context.

For this project, the source material is deliberately narrow: official Singapore legal and public-service pages. If the system cannot retrieve a relevant official source, it refuses instead of letting the model improvise.

## What works now

- Loads source chunks from JSONL
- Rejects source URLs outside approved official domains
- Retrieves matching source chunks with a lightweight keyword baseline
- Builds a grounded OpenAI prompt with source titles and URLs
- Refuses unrelated, foreign-law, or personal legal-strategy questions before calling the model
- Runs as a Telegram bot using environment variables
- Includes unit tests for retrieval, source validation, refusal behaviour, model-call behaviour, and evaluation scoring
- Includes a Stage 1 benchmark harness for retrieval, refusal, citation, disclaimer, and keyword checks

Approved domains for the seed dataset:

- `sso.agc.gov.sg`
- `agc.gov.sg`
- `judiciary.gov.sg`
- `mlaw.gov.sg`
- `lab.mlaw.gov.sg`

## How it works

```text
User question
    ↓
LegalRAGAssistant.retrieve()
    ↓
Source context selected from data/official_sources.jsonl
    ↓
prepare_answer()
    ├── grounded: build OpenAI messages with citations
    └── ungrounded: refuse without calling the model
    ↓
Telegram bot sends the answer
```

## Files

```text
chatbot.py                    Telegram/OpenAI wiring
legal_rag/core.py             Retrieval, grounding, prompt construction
legal_rag/sources.py          JSONL loader and official-domain checks
legal_rag/evaluation.py       Deterministic benchmark scoring
data/official_sources.jsonl   Seed official source records
eval/benchmark_questions.jsonl Stage 1 benchmark questions
eval/run_eval.py              Evaluation runner
eval/report.md                Latest generated evaluation report
tests/                        Unit tests
PROJECT_STATE.md              Working notes
```

## Run the tests

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

## Run the evaluation harness

```bash
python3 eval/run_eval.py
```

The Stage 1 harness does not call the language model. It checks the deterministic RAG layer:

- answerable Singapore legal questions retrieve the expected official source domain
- off-topic questions are refused
- foreign-law questions are refused
- personal legal-strategy questions are refused
- grounded prompts include citations and the legal disclaimer

Latest Stage 1 result:

```text
20 benchmark questions
20 passed, 0 failed
Retrieval accuracy: 100.0%
Refusal accuracy: 100.0%
Citation compliance: 100.0%
Disclaimer compliance: 100.0%
```

This result is for the current seed dataset. It is useful, but not final proof of legal quality. The next step is a larger benchmark and more source chunks.

## Source data format

Each line in `data/official_sources.jsonl` is one source chunk:

```json
{"id":"lab-legal-aid","title":"Legal Aid Bureau - Applying for legal aid","source":"Legal Aid Bureau","url":"https://lab.mlaw.gov.sg/legal-services/apply-for-legal-aid/","text":"The Legal Aid Bureau explains how eligible persons may apply for civil legal aid in Singapore.","tags":["legal aid","civil"]}
```

The loader rejects unofficial domains. That prevents blog posts, forum comments, or random summaries from quietly becoming legal context.

## Run the bot

Set the secrets locally. Do not commit them.

```bash
export TELEGRAM_TOKEN="your-telegram-token"
export OPENAI_API_KEY="your-openai-key"
export OPENAI_MODEL="gpt-4o-mini"
export BOT_USERNAME="@LegalCodebreakerBot"

python3 chatbot.py
```

## Disclaimer

This project provides general legal information only. It is not legal advice and is not a substitute for a qualified Singapore lawyer.
