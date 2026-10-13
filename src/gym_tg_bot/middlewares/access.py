from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from gym_tg_bot.access import AccessPolicy


class AccessMiddleware(BaseMiddleware):
    """Silently drops messages outside the allowed channel, chat and user."""

    def __init__(self, policy: AccessPolicy) -> None:
        self._policy = policy

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and not self._policy.is_allowed(event):
            structlog.get_logger().debug(
                "ignoring message outside the allowed scope",
                chat_id=event.chat.id,
                user_id=event.from_user.id if event.from_user else None,
                message_id=event.message_id,
            )
            return None
        return await handler(event, data)
