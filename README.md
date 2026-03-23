# 🧠 DexMind — Telegram AI Agent

> A smart, personal AI assistant on Telegram — powered by **OpenRouter.ai** free LLMs and deployed on **Railway**.

---

## ✨ Features

- 🧠 **Session Memory** — remembers last 5 conversations per user
- 🌦 **Live Weather** — just mention a city (e.g. *weather in Mumbai*)
- 🕐 **Date & Time** — real-time IST date/time support
- 🔀 **Switchable AI Model** — change model via Railway env variable, no code edit needed
- ⚡ **Crash-proof** — async, non-blocking, fully error-handled

---

## 🚀 Commands

| Command | Description |
|---|---|
| `/start` | Welcome message |
| `/help` | Show all commands |
| `/clear` | Clear your chat history |
| `/model` | Show current AI model |
| `/datetime` | Current IST date & time |
| `/developer` | Developer info |

---

## 🛠 Setup & Deploy (Railway)

**1. Clone the repo**
```bash
git clone https://github.com/yourusername/dexmind-bot.git
cd dexmind-bot
```

**2. Set environment variables in Railway dashboard**

| Variable | Value |
|---|---|
| `TELEGRAM_TOKEN` | Your bot token from [@BotFather](https://t.me/BotFather) |
| `OPENROUTER_API_KEY` | From [openrouter.ai](https://openrouter.ai) |
| `MODEL` | e.g. `mistralai/mistral-7b-instruct:free` |

**3. Deploy** — Railway auto-deploys on every push. Done! ✅

---

## 🤖 Free Models (OpenRouter)

```
mistralai/mistral-7b-instruct:free
meta-llama/llama-3-8b-instruct:free
google/gemma-3-4b-it:free
more free models available
```

Change model anytime from Railway Variables — no redeploy needed.

---

## 📦 Requirements

```
python-telegram-bot==21.6
openai==1.51.0
requests==2.32.3
```

---

## 👨‍💻 Developer

**PraX** — [@Dex_Error_404](https://t.me/Dex_Error_404)

Bot Version: `3.23.26`
