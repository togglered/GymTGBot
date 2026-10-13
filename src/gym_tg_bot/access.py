from dataclasses import dataclass

from aiogram.types import Message, MessageOriginChannel


@dataclass(frozen=True)
class AccessPolicy:
    """Decides which Telegram messages the bot is allowed to react to.

    Channel posts reach the bot as automatic forwards into the discussion chat. They have no
    human author (Telegram sets the sender to a service account), so they are checked by
    channel. Everything else in the discussion chat is checked by the author.

    Messages written as the discussion chat itself are what anonymous admins produce: Telegram
    hides which admin wrote them, so they cannot be checked by user and are accepted as is.
    """

    channel_id: int
    chat_id: int
    user_id: int

    def is_allowed(self, message: Message) -> bool:
        if message.chat.id != self.chat_id:
            return False
        if message.is_automatic_forward:
            return self._is_from_channel(message)
        if message.sender_chat is not None and message.sender_chat.id == self.chat_id:
            return True
        return message.from_user is not None and message.from_user.id == self.user_id

    def _is_from_channel(self, message: Message) -> bool:
        origin = message.forward_origin
        if isinstance(origin, MessageOriginChannel):
            return origin.chat.id == self.channel_id
        return message.sender_chat is not None and message.sender_chat.id == self.channel_id
