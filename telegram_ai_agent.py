"""
Telegram AI Agent using OpenRouter.ai (Free Models)
====================================================
Features:
  - Chat with a free LLM via OpenRouter
  - Detects weather questions and fetches live weather (wttr.in)
  - Remembers short conversation history per user

Requirements:
    pip install python-telegram-bot openai requests

Setup:
    1. Create a Telegram bot → talk to @BotFather → copy the token
    2. Get a free OpenRouter API key → https://openrouter.ai/keys
    3. Fill in TELEGRAM_TOKEN and OPENROUTER_API_KEY below
"""

import os
import re
import logging
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

# Validate env vars on startup (Railway will show this in deploy logs)
if not TELEGRAM_TOKEN:
    raise EnvironmentError("❌ TELEGRAM_TOKEN is not set in environment variables!")
if not OPENROUTER_API_KEY:
    raise EnvironmentError("❌ OPENROUTER_API_KEY is not set in environment variables!")

# Free models on OpenRouter (pick one):
#   "mistralai/mistral-7b-instruct:free"
#   "meta-llama/llama-3-8b-instruct:free"
#   "google/gemma-3-4b-it:free"
MODEL = "mistralai/mistral-7b-instruct:free"

SYSTEM_PROMPT = (
    "You are a helpful and friendly AI assistant in a Telegram chat. "
    "Answer clearly and concisely. "
    "If the user asks about weather and you receive weather data, "
    "summarise it in a friendly way."
)

# How many previous messages to keep per user (pairs = user + assistant)
MAX_HISTORY_PAIRS = 5

# ─────────────────────────── CLIENTS ──────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

openai_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# In-memory conversation history  {user_id: [{"role": ..., "content": ...}, ...]}
user_histories: dict[int, list[dict]] = {}

# ─────────────────────────── WEATHER ──────────────────────────────────────────

WEATHER_PATTERN = re.compile(
    r"\b(weather|temperature|forecast|rain|sunny|cloudy|hot|cold|humid)\b",
    re.IGNORECASE,
)

LOCATION_PATTERN = re.compile(
    r"\bin\s+([A-Za-z\s]+?)(?:[?!.,]|$)", re.IGNORECASE
)


def fetch_weather(location: str = "auto") -> str:
    """Fetch current weather from wttr.in (no API key needed)."""
    try:
        url = f"https://wttr.in/{requests.utils.quote(location)}?format=3"
        resp = requests.get(url, timeout=6)
        resp.raise_for_status()
        return resp.text.strip()
    except Exception as exc:
        logger.warning("Weather fetch failed: %s", exc)
        return ""


def extract_location(text: str) -> str:
    """Try to pull a city/location from the user's message."""
    match = LOCATION_PATTERN.search(text)
    if match:
        return match.group(1).strip()
    return "auto"   # wttr.in auto-detects by IP when location is empty


def build_weather_context(user_text: str) -> str:
    """Return a weather snippet to inject into the prompt, or empty string."""
    if not WEATHER_PATTERN.search(user_text):
        return ""
    location = extract_location(user_text)
    data = fetch_weather(location)
    if data:
        return f"[Live weather data: {data}]"
    return ""

# ─────────────────────────── AI REPLY ─────────────────────────────────────────

def get_ai_reply(user_id: int, user_text: str) -> str:
    """Send message to OpenRouter and return the assistant's reply."""
    history = user_histories.setdefault(user_id, [])

    # Optionally prepend live weather context
    weather_ctx = build_weather_context(user_text)
    content = f"{weather_ctx}\n{user_text}".strip() if weather_ctx else user_text

    history.append({"role": "user", "content": content})

    # Trim history to avoid token overflow
    if len(history) > MAX_HISTORY_PAIRS * 2:
        history[:] = history[-(MAX_HISTORY_PAIRS * 2):]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    try:
        response = openai_client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=512,
            temperature=0.7,
        )
        reply = response.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("OpenRouter error: %s", exc)
        reply = "⚠️ Sorry, I couldn't reach the AI service right now. Please try again."

    history.append({"role": "assistant", "content": reply})
    return reply

# ─────────────────────────── HANDLERS ─────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    name = update.effective_user.first_name or "there"
    await update.message.reply_text(
        f"👋 Hey {name}! I'm your AI assistant.\n\n"
        "Ask me anything — for example:\n"
        "  • *What's the weather in London?*\n"
        "  • *Tell me a fun fact*\n"
        "  • *Help me write an email*\n\n"
        "Type /help for more commands.",
        parse_mode="Markdown",
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🤖 *AI Agent Commands*\n\n"
        "/start – Welcome message\n"
        "/help  – Show this help\n"
        "/clear – Clear your conversation history\n\n"
        "Just send any message to chat with the AI!\n"
        "Ask about weather with a city name for live results.",
        parse_mode="Markdown",
    )


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_histories.pop(user_id, None)
    await update.message.reply_text("🗑️ Conversation history cleared!")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id   = update.effective_user.id
    user_text = update.message.text or ""

    if not user_text.strip():
        return

    # Show typing indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    reply = get_ai_reply(user_id, user_text)
    await update.message.reply_text(reply)

# ─────────────────────────── MAIN ─────────────────────────────────────────────

def main() -> None:
    logger.info("Starting Telegram AI Agent…")
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot is running. Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
