from collections import defaultdict, deque
from typing import Literal, TypedDict

_MAX_HISTORY = 20


class HistoryItem(TypedDict):
    role: Literal["user", "assistant"]
    content: str


class ThreadMemory:
    def __init__(self) -> None:
        self._store: defaultdict[tuple[int, int], deque[HistoryItem]] = defaultdict(
            lambda: deque(maxlen=_MAX_HISTORY)
        )

    def add(
        self, chat_id: int, thread_id: int, role: Literal["user", "assistant"], content: str
    ) -> None:
        history_item = HistoryItem(role=role, content=content)
        self._store[(chat_id, thread_id)].append(history_item)

    def get(self, chat_id: int, thread_id: int) -> list[HistoryItem]:
        return list(self._store.get((chat_id, thread_id)) or [])
