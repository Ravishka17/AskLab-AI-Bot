from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque


@dataclass
class ChatMessage:
    role: str
    content: str


class HistoryStore:
    def __init__(self, *, max_messages: int) -> None:
        self._max_messages = max_messages
        self._history: dict[int, Deque[ChatMessage]] = defaultdict(
            lambda: deque(maxlen=max_messages)
        )

    def get(self, key: int) -> list[ChatMessage]:
        return list(self._history[key])

    def append(self, key: int, message: ChatMessage) -> None:
        self._history[key].append(message)

    def clear(self, key: int) -> None:
        self._history[key].clear()
