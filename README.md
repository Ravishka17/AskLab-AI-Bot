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

If your host expects an "app file" (a single Python file to run), this repo includes entrypoints at the project root.

Recommended settings:

- **App py file:** `main.py`
  - Alternatives: `app.py` or `asklab_ai_bot/__main__.py`
- **Requirements file:** `requirements.txt`
- **Additional Python packages:** `asklab_ai_bot`
  - This tells the hosting panel to install the local `asklab_ai_bot` package so it can be imported by the entrypoint files

If you see `can't open file '/home/container/main.py'`, it means the panel can't find the file at that exact path.

- Open your server's file manager and confirm you see `main.py` directly inside `/home/container/`.
- If your files are inside a folder (for example `/home/container/AskLab-AI-Bot/`), set **App py file** to include that folder name (e.g. `AskLab-AI-Bot/main.py`).

If you see `ModuleNotFoundError: No module named 'asklab_ai_bot'`:

- In the **Startup** tab, add `asklab_ai_bot` to the **Additional Python packages** field
- This ensures the local package is installed in editable mode so Python can find it

## Usage

- Ask a question:
  - `!ask Explain retrieval-augmented generation in simple terms`
- Clear memory in the current channel:
  - `!reset`
