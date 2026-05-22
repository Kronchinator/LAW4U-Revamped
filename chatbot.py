from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# --- Placeholders ---
TELEGRAM_TOKEN: Final = "YOUR_TELEGRAM_BOT_TOKEN"
OPENAI_API_KEY: Final = "YOUR_OPENAI_API_KEY"
BOT_USERNAME: Final = "@LegalCodebreakerBot"

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """You are a Singaporean legal assistant with deep knowledge of Singapore law.

Your job is to answer questions about the Singapore legal system clearly and accurately.

Rules you must follow:
1. Only answer questions related to Singapore law, the legal system, courts, or legal procedures.
2. Base your answers exclusively on official Singapore sources:
   - Singapore Statutes Online (sso.agc.gov.sg)
   - Attorney-General's Chambers (agc.gov.sg)
   - Singapore Judiciary (judiciary.gov.sg)
   - Ministry of Law (mlaw.gov.sg)
   - Legal Aid Bureau (lab.mlaw.gov.sg)
3. Always cite the specific Act, section, or penal code you are referencing (e.g. "Penal Code 1871, s 304A" or "Criminal Procedure Code 2010, s 23").
4. Include the relevant URL from the above official sources when possible.
5. If a question is outside Singapore law or you cannot find reliable official grounding, say so clearly and recommend the user consult a qualified Singapore lawyer.
6. Never give personal legal advice. Always end with a reminder that this is general information only and not a substitute for professional legal counsel.
7. Keep responses clear and structured — use numbered lists or sections when helpful.

If the user asks something unrelated to Singapore law, politely redirect them."""


def query_openai(user_message: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_tokens=1024,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI error: {e}")
        return "Sorry, I ran into an error fetching a response. Please try again shortly."


# Commands

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! I'm LegalCodebreaker 🇸🇬\n\n"
        "I can answer questions about the Singapore legal system — laws, courts, penal codes, and procedures.\n\n"
        "Ask me anything, and I'll cite official sources where possible.\n\n"
        "⚠️ I provide general information only — not professional legal advice. For serious matters, consult a qualified lawyer."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Here are some things you can ask me:\n"
        "• What is the penalty for theft in Singapore?\n"
        "• How does bail work in Singapore courts?\n"
        "• What does the Misuse of Drugs Act cover?\n"
        "• How do I file a civil claim in the Magistrates' Court?\n\n"
        "For urgent legal issues, contact the Legal Aid Bureau (lab.mlaw.gov.sg) or a practising Singapore lawyer."
    )


# Message handler

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f"User ({update.message.chat.id}) in {message_type}: {text}")

    if message_type == "group":
        if BOT_USERNAME in text:
            text = text.replace(BOT_USERNAME, "").strip()
        else:
            return

    response = query_openai(text)
    print(f"Bot: {response}")
    await update.message.reply_text(response)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error: {context.error}")


if __name__ == "__main__":
    print("Starting LegalCodebreaker bot...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.add_error_handler(error_handler)

    print("Polling started...")
    app.run_polling(poll_interval=1)
