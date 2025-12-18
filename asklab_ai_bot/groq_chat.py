from __future__ import annotations

import asyncio

from groq import Groq

from .config import Settings


class GroqChat:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = Groq(api_key=settings.groq_api_key)

    def _complete_sync(self, messages: list[dict[str, str]]) -> str:
        completion = self._client.chat.completions.create(
            model=self._settings.groq_model,
            messages=messages,
            temperature=self._settings.groq_temperature,
            max_tokens=self._settings.groq_max_tokens,
        )

        choice = completion.choices[0]
        content = getattr(choice.message, "content", None)
        if not content:
            raise RuntimeError("Groq returned an empty response")
        return content

    async def complete(self, messages: list[dict[str, str]]) -> str:
        try:
            return await asyncio.to_thread(self._complete_sync, messages)
        except Exception as exc:
            raise RuntimeError(f"Groq request failed: {exc}") from exc


def to_groq_messages(system_prompt: str, history: list[dict[str, str]]) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    return messages
