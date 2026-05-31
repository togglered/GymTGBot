import json
import time
from dataclasses import asdict
from pathlib import Path

import aiosqlite

from gym_tg_bot.chat import ChatMessage, ToolCall, ToolResult


class ThreadMemory:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    async def ensure_schema(self) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    thread_id INTEGER NOT NULL,
                    kind TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                )
                """
            )
            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS ix_messages_thread
                ON messages (chat_id, thread_id, id)
                """
            )
            await db.commit()

    async def add(
        self,
        chat_id: int,
        thread_id: int,
        item: ChatMessage | ToolCall | ToolResult,
    ) -> None:
        payload = json.dumps(asdict(item))
        created_at = int(time.time())
        match item:
            case ChatMessage():
                kind = "chat"
            case ToolCall():
                kind = "tool_call"
            case ToolResult():
                kind = "tool_result"
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "INSERT INTO messages (chat_id, thread_id, kind, payload, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (chat_id, thread_id, kind, payload, created_at),
            )
            await db.commit()

    async def get(self, chat_id: int, thread_id: int) -> list[ChatMessage | ToolCall | ToolResult]:
        async with aiosqlite.connect(self._db_path) as db:
            statement = """
                SELECT kind, payload FROM messages
                WHERE chat_id = ? AND thread_id = ?
                ORDER BY id ASC
            """
            params = (chat_id, thread_id)
            async with db.execute(statement, params) as cursor:
                rows = await cursor.fetchall()
                result: list[ChatMessage | ToolCall | ToolResult] = []
                for kind, payload in rows:
                    data = json.loads(payload)
                    match kind:
                        case "chat":
                            result.append(ChatMessage(**data))
                        case "tool_call":
                            result.append(ToolCall(**data))
                        case "tool_result":
                            result.append(ToolResult(**data))
                        case _:
                            raise ValueError(f"unknown kind: {kind}")
            return result
