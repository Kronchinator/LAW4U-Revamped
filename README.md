# LegalCodebreaker: Singapore legal RAG assistant

LegalCodebreaker answers Singapore legal information questions only after it retrieves relevant official sources.

The first version was a Telegram bot with a long system prompt. That was too easy to fool and too hard to measure. This version moves the important parts into a small RAG core: official-source validation, retrieval, prompt construction, citations, refusal behaviour, and a deterministic evaluation harness.

Current status: working MVP foundation. It is not a full legal database.

## Why I built it this way

Legal chatbots are risky because a model can sound confident while making things up. For law, that is a bad failure mode.

The rule here is simple: if the system cannot retrieve an approved Singapore source, it does not ask the model to answer.

That guardrail is the main point of the project. The bot validates sources, retrieves relevant context, refuses questions outside its evidence base, and then tests whether those behaviours work.

## What RAG means here

RAG means retrieval augmented generation. The model does not answer from memory alone. The system first retrieves source material, then gives that material to the model as context.

For this project, the source material is deliberately narrow: official Singapore legal and public-service pages. If the question falls outside that source set, the system refuses instead of improvising.

## What works now

- Loads source chunks from JSONL
- Rejects source URLs outside approved official domains
- Retrieves matching chunks with a lightweight keyword baseline
- Builds grounded OpenAI prompts with source titles and URLs
- Refuses unrelated, foreign-law, or personal legal-strategy questions before calling the model
- Runs as a Telegram bot through environment variables
- Includes unit tests for retrieval, source validation, refusal behaviour, model-call behaviour, and evaluation scoring
- Includes an AI Trust Lab benchmark for retrieval, refusal, prompt-injection resistance, citation, disclaimer, and keyword checks
- Generates both a Markdown evaluation report and a static HTML dashboard

Approved domains in the seed dataset:

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
chatbot.py                     Telegram/OpenAI wiring
legal_rag/core.py              Retrieval, grounding, prompt construction
legal_rag/sources.py           JSONL loader and official-domain checks
legal_rag/evaluation.py        Deterministic benchmark scoring
data/official_sources.jsonl    Seed official source records
eval/benchmark_questions.jsonl Stage 1 benchmark questions
eval/run_eval.py               Evaluation runner
eval/report.md                 Latest generated evaluation report
eval/trust_dashboard.html      Static AI Trust Lab dashboard
tests/                         Unit tests
PROJECT_STATE.md               Working notes
```

## Run the tests

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

## Run the AI Trust Lab evaluation

```bash
python3 eval/run_eval.py
```

The AI Trust Lab harness does not call the language model. It checks the deterministic RAG layer:

- answerable Singapore legal questions retrieve the expected official source domain
- off-topic questions are refused
- foreign-law questions are refused
- personal legal-strategy questions are refused
- prompt-injection attempts are refused
- grounded prompts include citations and the legal disclaimer

It writes two artifacts:

```text
eval/report.md
eval/trust_dashboard.html
```

Latest Stage 1 result:

```text
40 benchmark questions
40 passed, 0 failed
Retrieval accuracy: 100.0%
Refusal accuracy: 100.0%
Citation compliance: 100.0%
Disclaimer compliance: 100.0%
```

This result is for the current seed dataset. It is useful, but it is not proof of legal quality. The point is to show that the safety layer can be measured instead of trusted by assumption.

## Source data format

Each line in `data/official_sources.jsonl` is one source chunk:

```json
{"id":"lab-legal-aid","title":"Legal Aid Bureau - Applying for legal aid","source":"Legal Aid Bureau","url":"https://lab.mlaw.gov.sg/legal-services/apply-for-legal-aid/","text":"The Legal Aid Bureau explains how eligible persons may apply for civil legal aid in Singapore.","tags":["legal aid","civil"]}
```

The loader rejects unofficial domains so blog posts, forum comments, or random summaries cannot quietly become legal context.

## Run the bot

Set secrets locally. Do not commit them.

```bash
export TELEGRAM_TOKEN="your-telegram-token"
export OPENAI_API_KEY="your-openai-key"
export OPENAI_MODEL="gpt-4o-mini"
export BOT_USERNAME="@LegalCodebreakerBot"

python3 chatbot.py
```

## Disclaimer

This project provides general legal information only. It is not legal advice and is not a substitute for a qualified Singapore lawyer.
