"""Telegram entrypoint for LegalCodebreaker.

The RAG logic lives in ``legal_rag`` so it can be tested without Telegram or
OpenAI. This file wires that core into a Telegram bot when credentials exist.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Final

from legal_rag.core import LegalRAGAssistant
from legal_rag.sources import load_jsonl_sources

BOT_USERNAME: Final = os.getenv("BOT_USERNAME", "@LegalCodebreakerBot")
DEFAULT_MODEL: Final = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_SOURCES_PATH: Final = str(
    Path(__file__).resolve().parent / "data" / "official_sources.jsonl"
)


def build_assistant(source_path: str | Path = DEFAULT_SOURCES_PATH) -> LegalRAGAssistant:
    """Build the RAG assistant from validated official-source records."""

    return LegalRAGAssistant(load_jsonl_sources(source_path), min_score=1)


def query_openai(
    user_message: str,
    client: Any,
    assistant: LegalRAGAssistant,
    model: str = DEFAULT_MODEL,
) -> str:
    """Prepare a grounded RAG prompt and send it to OpenAI.

    If retrieval cannot ground the question in official Singapore legal sources,
    return the refusal directly without calling the model.
    """

    prepared = assistant.prepare_answer(user_message)
    if not prepared.can_answer:
        return prepared.message

    try:
        response = client.chat.completions.create(
            model=model,
            messages=prepared.messages,
            max_tokens=900,
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:  # pragma: no cover - defensive runtime guard
        print(f"OpenAI error: {exc}")
        return "Sorry, I ran into an error fetching a grounded response. Please try again shortly."


# Commands
async def start_command(update, context):
    await update.message.reply_text(
        "Hello! I'm LegalCodebreaker 🇸🇬\n\n"
        "I answer Singapore legal-information questions using retrieved official-source context.\n\n"
        "Ask about laws, courts, legal aid, or procedures and I will cite official sources where possible.\n\n"
        "⚠️ I provide general information only — not professional legal advice. For serious matters, consult a qualified lawyer."
    )


async def help_command(update, context):
    await update.message.reply_text(
        "Good questions to try:\n"
        "• How do I apply for legal aid in Singapore?\n"
        "• What are Small Claims Tribunals for?\n"
        "• Where can I read about theft under the Penal Code?\n"
        "• What happens in a criminal court process?\n\n"
        "For urgent legal issues, contact the Legal Aid Bureau (lab.mlaw.gov.sg) or a practising Singapore lawyer."
    )


async def handle_message(update, context):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f"User ({update.message.chat.id}) in {message_type}: {text}")

    if message_type in {"group", "supergroup"}:
        if BOT_USERNAME in text:
            text = text.replace(BOT_USERNAME, "").strip()
        else:
            return

    response = query_openai(text, context.bot_data["openai_client"], context.bot_data["rag_assistant"])
    print(f"Bot: {response}")
    await update.message.reply_text(response)


async def error_handler(update, context):
    print(f"Update {update} caused error: {context.error}")


def main() -> None:
    telegram_token = os.environ["TELEGRAM_TOKEN"]
    openai_api_key = os.environ["OPENAI_API_KEY"]

    from openai import OpenAI
    from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

    # Bind annotations at runtime for python-telegram-bot users without making
    # tests import that dependency.
    _ = ContextTypes

    print("Starting LegalCodebreaker bot...")
    app = Application.builder().token(telegram_token).build()
    app.bot_data["openai_client"] = OpenAI(api_key=openai_api_key)
    app.bot_data["rag_assistant"] = build_assistant()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.add_error_handler(error_handler)

    print("Polling started...")
    app.run_polling(poll_interval=1)


if __name__ == "__main__":
    main()
