"""
Telegram AI Agent using OpenRouter.ai (Free Models)
====================================================
- python-telegram-bot==21.6  (Python 3.13 compatible)
- OpenRouter free LLM
- Live weather via wttr.in (no API key needed)
- Per-user conversation history
- Crash-proof error handling
"""

import os
import re
import logging
import asyncio
import urllib.parse
from functools import partial

import requests
from openai import OpenAI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ─────────────────────────── CONFIG ───────────────────────────────────────────

TELEGRAM_TOKEN     = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Model ab Railway environment variable se aayega
# Railway me MODEL variable set karo, jaise:
#   mistralai/mistral-7b-instruct:free
#   meta-llama/llama-3-8b-instruct:free
#   google/gemma-3-4b-it:free
# Agar MODEL set nahi hai toh default fallback use hoga
MODEL = os.getenv("MODEL", "mistralai/mistral-7b-instruct:free")

if not TELEGRAM_TOKEN:
    raise EnvironmentError("❌ TELEGRAM_TOKEN is not set in Railway Variables!")
if not OPENROUTER_API_KEY:
    raise EnvironmentError("❌ OPENROUTER_API_KEY is not set in Railway Variables!")

SYSTEM_PROMPT = (
    "You are a helpful and friendly AI assistant inside a Telegram chat. "
    "Keep answers clear and concise. "
    "If weather data is provided in the message, summarise it naturally."
)

MAX_HISTORY_PAIRS = 5   # remember last N question-answer pairs per user

# ─────────────────────────── LOGGING ──────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Model ko startup pe log karo — Railway logs me dikh jayega
logger.info("Using model: %s", MODEL)

# ─────────────────────────── OPENROUTER CLIENT ────────────────────────────────

ai_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Per-user message history  { user_id: [ {role, content}, ... ] }
user_histories: dict[int, list[dict]] = {}

# ─────────────────────────── WEATHER HELPER ───────────────────────────────────

_WEATHER_RE  = re.compile(
    r"\b(weather|temperature|forecast|rain|sunny|cloudy|hot|cold|humid)\b",
    re.IGNORECASE,
)
_LOCATION_RE = re.compile(r"\bin\s+([A-Za-z\s]+?)(?:[?!.,]|$)", re.IGNORECASE)


def _fetch_weather(location: str = "") -> str:
    try:
        url = f"https://wttr.in/{urllib.parse.quote(location)}?format=3"
        r = requests.get(url, timeout=6)
        r.raise_for_status()
        return r.text.strip()
    except Exception as e:
        logger.warning("Weather fetch failed: %s", e)
        return ""


def _weather_context(text: str) -> str:
    if not _WEATHER_RE.search(text):
        return ""
    m = _LOCATION_RE.search(text)
    loc = m.group(1).strip() if m else ""
    data = _fetch_weather(loc)
    return f"[Live weather: {data}]" if data else ""

# ─────────────────────────── AI CALL (non-blocking) ───────────────────────────

def _sync_call(messages: list[dict]) -> str:
    """Blocking OpenRouter call — always run via run_in_executor."""
    resp = ai_client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=512,
        temperature=0.7,
    )
    content = resp.choices[0].message.content
    return content.strip() if content else "⚠️ Empty response from AI. Please try again."


async def get_ai_reply(user_id: int, user_text: str) -> str:
    history = user_histories.setdefault(user_id, [])

    ctx     = _weather_context(user_text)
    content = f"{ctx}\n{user_text}".strip() if ctx else user_text
    history.append({"role": "user", "content": content})

    # Trim to avoid token overflow
    if len(history) > MAX_HISTORY_PAIRS * 2:
        history[:] = history[-(MAX_HISTORY_PAIRS * 2):]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    try:
        loop  = asyncio.get_event_loop()
        reply = await loop.run_in_executor(None, partial(_sync_call, messages))
    except Exception as e:
        logger.error("OpenRouter error: %s", e)
        history.pop()   # remove failed user message to keep history clean
        return "⚠️ Couldn't reach the AI right now. Please try again in a moment."

    history.append({"role": "assistant", "content": reply})
    return reply

# ─────────────────────────── TELEGRAM HANDLERS ────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    name = update.effective_user.first_name or "there"
    await update.message.reply_text(
        f"👋 Hey {name}! I'm your AI assistant.\n\n"
        "Try asking:\n"
        "• What's the weather in Mumbai?\n"
        "• Tell me a fun fact\n"
        "• Help me write an email\n\n"
        "Commands: /help  /clear  /model"
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🤖 AI Agent Commands\n\n"
        "/start – Welcome message\n"
        "/help  – Show this help\n"
        "/clear – Clear your chat history\n"
        "/model – Show current AI model\n\n"
        "Just type anything to chat with the AI!\n"
        "Include a city name for live weather."
    )


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_histories.pop(update.effective_user.id, None)
    await update.message.reply_text("🗑️ Your conversation history has been cleared!")


async def cmd_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show which model is currently active."""
    await update.message.reply_text(f"🤖 Current model:\n`{MODEL}`", parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    user_text = update.message.text.strip()
    if not user_text:
        return

    try:
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id, action="typing"
        )
        reply = await get_ai_reply(update.effective_user.id, user_text)
        await update.message.reply_text(reply)

    except Exception as e:
        logger.error("Unhandled handler error: %s", e)
        await update.message.reply_text(
            "⚠️ Something went wrong. Please try again."
        )

# ─────────────────────────── MAIN ─────────────────────────────────────────────

def main() -> None:
    logger.info("Starting Telegram AI Agent (PTB 21.6 / Python 3.13)…")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(CommandHandler("model", cmd_model))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot is running. Listening for messages…")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
