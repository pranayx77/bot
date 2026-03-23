# 🤖 Telegram AI Agent

A smart Telegram chatbot powered by **OpenRouter.ai** free LLMs, deployed on **Railway**.

---

## ✨ Features

- 🧠 **Session Memory** — remembers last 5 conversations per user
- 🔀 **Switchable AI Model** — change model via Railway env variable, no code edit needed
- ⚡ **Crash-proof** — async, non-blocking, error-handled

---

## 🚀 Commands

| Command | Description |
|---|---|
| `/start` | Welcome message |
| `/help` | Show all commands |
| `/clear` | Clear chat history |
| `/model` | Show current AI model |
| `/datetime` | Current IST date & time |
| `/developer` | Developer info |

---

## 🛠 Setup & Deploy (Railway)

**1. Clone the repo**
```bash
git clone https://github.com/yourusername/telegram-ai-agent.git
cd telegram-ai-agent
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
more free models
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
