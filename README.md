# LegalCodebreaker: Singapore legal RAG assistant

LegalCodebreaker answers Singapore legal information questions using retrieved official sources before it calls an LLM.

The first version of this repo was a simple Telegram bot with a long system prompt. This version moves the important parts into a small RAG core: source validation, retrieval, prompt building, citations, and refusal when the bot cannot ground a question.

Current status: working MVP foundation. It is not a full legal database yet.

## Why I built it this way

Legal chatbots can be risky. If a model guesses, the answer may sound confident and still be wrong.

So the rule here is simple:

**No official Singapore source retrieved → no model answer.**

That keeps the bot honest. It also makes the project more than a Telegram wrapper around OpenAI. The interesting part is the guardrail: validate the sources, retrieve the relevant context, and refuse when the question falls outside the available evidence.

## What works now

- Loads source chunks from JSONL
- Rejects source URLs outside approved official domains
- Retrieves matching source chunks with a lightweight keyword baseline
- Builds a grounded OpenAI prompt with source titles and URLs
- Refuses unrelated or ungrounded questions before calling the model
- Runs as a Telegram bot using environment variables
- Includes unit tests for retrieval, source validation, refusal behaviour, and model-call behaviour

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

## What is a RAG

"RAG stands for Retrieval-Augmented Generation. It is an AI technique that grounds a large language model (LLM) in external, proprietary, or up-to-date data before generating a response. Think of it like an open-book exam for the AI—it searches a trusted database to find the right information, then reads it to craft an accurate answer." - Amazon Web Services


## Files

```text
chatbot.py                    Telegram/OpenAI wiring
legal_rag/core.py             Retrieval, grounding, prompt construction
legal_rag/sources.py          JSONL loader and official-domain checks
data/official_sources.jsonl   Seed official source records
tests/                        Unit tests
PROJECT_STATE.md              Working notes
```

## Run the tests

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

## Source data format

Each line in `data/official_sources.jsonl` is one source chunk:

```json
{"id":"lab-legal-aid","title":"Legal Aid Bureau - Applying for legal aid","source":"Legal Aid Bureau","url":"https://lab.mlaw.gov.sg/legal-services/apply-for-legal-aid/","text":"The Legal Aid Bureau explains how eligible persons may apply for civil legal aid in Singapore.","tags":["legal aid","civil"]}
```

The loader rejects unofficial domains. That prevents blog posts, forum comments, or random summaries from invading the bot's context which also helps with negating AI hallucination.

## Disclaimer

This project provides general legal information only. It is not legal advice and is not a substitute for a qualified Singapore lawyer.
