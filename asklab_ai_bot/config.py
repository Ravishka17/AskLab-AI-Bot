from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    discord_bot_token: str
    groq_api_key: str
    groq_model: str
    system_prompt: str
    groq_temperature: float
    groq_max_tokens: int
    max_history_messages: int


def _get_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def get_settings() -> Settings:
    discord_bot_token = _get_env("DISCORD_BOT_TOKEN")
    groq_api_key = _get_env("GROQ_API_KEY")

    if not discord_bot_token:
        raise ValueError(
            "Missing DISCORD_BOT_TOKEN. Set it in your environment or in a .env file."
        )
    if not groq_api_key:
        raise ValueError(
            "Missing GROQ_API_KEY. Set it in your environment or in a .env file."
        )

    groq_model = _get_env("GROQ_MODEL") or "llama3-8b-8192"
    system_prompt = (
        _get_env("SYSTEM_PROMPT")
        or "You are AskLab AI, a helpful assistant inside a Discord server."
    )

    groq_temperature = float(_get_env("GROQ_TEMPERATURE") or 0.7)
    groq_max_tokens = int(_get_env("GROQ_MAX_TOKENS") or 1024)

    max_history_messages = int(_get_env("MAX_HISTORY_MESSAGES") or 12)

    return Settings(
        discord_bot_token=discord_bot_token,
        groq_api_key=groq_api_key,
        groq_model=groq_model,
        system_prompt=system_prompt,
        groq_temperature=groq_temperature,
        groq_max_tokens=groq_max_tokens,
        max_history_messages=max_history_messages,
    )
