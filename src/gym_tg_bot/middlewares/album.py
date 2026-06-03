import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject


class AlbumMiddleware(BaseMiddleware):
    def __init__(self, latency: float = 0.5):
        self._latency = latency
        self._buffer: dict[str, list[Message]] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message) or event.media_group_id is None:
            return await handler(event, data)

        key = event.media_group_id
        if key not in self._buffer:
            self._buffer[key] = [event]
            await asyncio.sleep(self._latency)
            album = self._buffer.pop(key)
            album.sort(key=lambda m: m.message_id)
            data["album"] = album
            return await handler(event, data)
        else:
            self._buffer[key].append(event)
            return
