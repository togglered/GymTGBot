from collections import defaultdict, deque

from gym_tg_bot.chat import ChatMessage, Role

_MAX_HISTORY = 20


class ThreadMemory:
    def __init__(self) -> None:
        self._store: defaultdict[tuple[int, int], deque[ChatMessage]] = defaultdict(
            lambda: deque(maxlen=_MAX_HISTORY)
        )

    def add(self, chat_id: int, thread_id: int, role: Role, content: str) -> None:
        msg = ChatMessage(role=role, content=content)
        self._store[(chat_id, thread_id)].append(msg)

    def get(self, chat_id: int, thread_id: int) -> list[ChatMessage]:
        return list(self._store.get((chat_id, thread_id)) or [])
