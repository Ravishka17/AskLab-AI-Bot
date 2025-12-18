# AskLab-AI-Bot

A Python Discord bot that replies using Groq's LLM API.

## Features

- `!ask <question>` command
- Mention the bot to ask a question (e.g. `@AskLabBot what is Groq?`)
- `!reset` to clear per-channel conversation memory

## Setup

### 1) Create a Discord bot

1. Go to the Discord Developer Portal and create an application + bot.
2. Copy the bot token.
3. Enable **Message Content Intent** (required for mention + prefix commands).
4. Invite the bot to your server.

### 2) Create a Groq API key

- Create an API key in the Groq console and read the docs:
  https://console.groq.com/docs/overview

### 3) Configure environment variables

Copy the example env file and fill in values:

```bash
cp .env.example .env
```

Required:

- `DISCORD_BOT_TOKEN`
- `GROQ_API_KEY`

Optional:

- `GROQ_MODEL` (default: `llama3-8b-8192`)
- `GROQ_TEMPERATURE` (default: `0.7`)
- `GROQ_MAX_TOKENS` (default: `1024`)

### 4) Install and run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python -m asklab_ai_bot
# or: python main.py
# or: python app.py
```

### Pterodactyl / panel hosting

If your host expects an “app file” (e.g. `main.py`), this repo includes both `main.py` and `app.py` at the project root.

- **App py file:** `main.py` (or `app.py`)
- If you still see `can't open file '/home/container/main.py'`, open your server's file manager and confirm `main.py` exists in `/home/container/` (not inside a nested folder like `/home/container/AskLab-AI-Bot/`).

## Usage

- Ask a question:
  - `!ask Explain retrieval-augmented generation in simple terms`
- Clear memory in the current channel:
  - `!reset`
