import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

import pytest
from aiogram import Bot, Dispatcher, Router
from aiogram.enums import MessageOriginType
from aiogram.filters import CommandStart
from aiogram.types import (
    Chat,
    Message,
    MessageOriginChannel,
    PhotoSize,
    Update,
    User,
)

from gym_tg_bot.access import AccessPolicy
from gym_tg_bot.middlewares.access import AccessMiddleware
from gym_tg_bot.middlewares.album import AlbumMiddleware

CHANNEL_ID = -1001111111111
CHAT_ID = -1002222222222
USER_ID = 42
STRANGER_ID = 43
TELEGRAM_SERVICE_ID = 777000
ANONYMOUS_ADMIN_ID = 1087968824
CHANNEL_BOT_ID = 136817688

POLICY = AccessPolicy(channel_id=CHANNEL_ID, chat_id=CHAT_ID, user_id=USER_ID)


def _user(user_id: int) -> User:
    return User(id=user_id, is_bot=False, first_name="x")


def _channel(channel_id: int) -> Chat:
    return Chat(id=channel_id, type="channel")


def _message(
    *,
    chat_id: int = CHAT_ID,
    chat_type: str = "supergroup",
    user_id: int | None = USER_ID,
    message_id: int = 1,
    **extra: object,
) -> Message:
    return Message(
        message_id=message_id,
        date=datetime.now(UTC),
        chat=Chat(id=chat_id, type=chat_type),
        from_user=_user(user_id) if user_id is not None else None,
        **extra,  # type: ignore[arg-type]
    )


def _channel_post(
    *,
    channel_id: int = CHANNEL_ID,
    chat_id: int = CHAT_ID,
    with_origin: bool = True,
    message_id: int = 1,
) -> Message:
    origin = (
        MessageOriginChannel(
            type=MessageOriginType.CHANNEL,
            date=datetime.now(UTC),
            chat=_channel(channel_id),
            message_id=5,
        )
        if with_origin
        else None
    )
    return _message(
        chat_id=chat_id,
        user_id=TELEGRAM_SERVICE_ID,
        message_id=message_id,
        is_automatic_forward=True,
        sender_chat=_channel(channel_id),
        forward_origin=origin,
    )


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        pytest.param(_message(), True, id="comment from the allowed user"),
        pytest.param(_message(user_id=STRANGER_ID), False, id="comment from a stranger"),
        pytest.param(_message(chat_id=-1009999999999), False, id="allowed user in another chat"),
        pytest.param(
            _message(chat_id=USER_ID, chat_type="private"), False, id="private chat with the bot"
        ),
        pytest.param(_message(user_id=None), False, id="no author at all"),
        pytest.param(_channel_post(), True, id="post from the allowed channel"),
        pytest.param(
            _channel_post(channel_id=-1003333333333), False, id="post from another channel"
        ),
        pytest.param(
            _channel_post(chat_id=-1009999999999), False, id="allowed channel, wrong chat"
        ),
        pytest.param(
            _channel_post(with_origin=False), True, id="allowed channel via sender_chat only"
        ),
        pytest.param(
            _channel_post(channel_id=-1003333333333, with_origin=False),
            False,
            id="another channel via sender_chat only",
        ),
        pytest.param(
            _message(
                user_id=ANONYMOUS_ADMIN_ID,
                sender_chat=Chat(id=CHAT_ID, type="supergroup"),
            ),
            True,
            id="anonymous admin, written as the chat itself",
        ),
        pytest.param(
            _message(
                user_id=ANONYMOUS_ADMIN_ID,
                sender_chat=Chat(id=-1009999999999, type="supergroup"),
            ),
            False,
            id="sent as some other group",
        ),
        pytest.param(
            _message(user_id=CHANNEL_BOT_ID, sender_chat=_channel(CHANNEL_ID)),
            False,
            id="comment written on behalf of the channel",
        ),
        pytest.param(
            _message(
                user_id=USER_ID,
                is_automatic_forward=True,
                sender_chat=_channel(-1003333333333),
            ),
            False,
            id="allowed user id does not grant channel access",
        ),
    ],
)
def test_policy(message: Message, expected: bool) -> None:
    assert POLICY.is_allowed(message) is expected


class _SpyAlbum(AlbumMiddleware):
    def __init__(self, latency: float) -> None:
        super().__init__(latency=latency)
        self.calls = 0

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        self.calls += 1
        return await super().__call__(*args, **kwargs)


class _Recorder:
    def __init__(self) -> None:
        self.messages: list[Message] = []
        self.albums: list[list[Message] | None] = []
        self.starts = 0


@pytest.fixture
async def bot() -> AsyncIterator[Bot]:
    bot = Bot(token="123456789:" + "A" * 35)
    yield bot
    await bot.session.close()


def _dispatcher(recorder: _Recorder, album: AlbumMiddleware) -> Dispatcher:
    router = Router()

    @router.message(CommandStart())
    async def on_start(message: Message) -> None:
        recorder.starts += 1

    @router.message()
    async def on_message(message: Message, album: list[Message] | None = None) -> None:
        recorder.messages.append(message)
        recorder.albums.append(album)

    dp = Dispatcher()
    dp.message.outer_middleware(AccessMiddleware(POLICY))
    dp.message.middleware(album)
    dp.include_router(router)
    return dp


async def _feed(dp: Dispatcher, bot: Bot, *messages: Message) -> None:
    await asyncio.gather(
        *(
            dp.feed_update(bot, Update(update_id=i, message=message))
            for i, message in enumerate(messages, 1)
        )
    )


async def test_allowed_user_reaches_the_handler(bot: Bot) -> None:
    recorder = _Recorder()
    dp = _dispatcher(recorder, AlbumMiddleware(latency=0.01))

    await _feed(dp, bot, _message(text="hello"))

    assert len(recorder.messages) == 1


async def test_stranger_never_reaches_the_handler(bot: Bot) -> None:
    recorder = _Recorder()
    dp = _dispatcher(recorder, AlbumMiddleware(latency=0.01))

    await _feed(dp, bot, _message(user_id=STRANGER_ID, text="hello"))

    assert recorder.messages == []


async def test_anonymous_admin_reaches_the_handler(bot: Bot) -> None:
    recorder = _Recorder()
    dp = _dispatcher(recorder, AlbumMiddleware(latency=0.01))

    await _feed(
        dp,
        bot,
        _message(
            user_id=ANONYMOUS_ADMIN_ID,
            sender_chat=Chat(id=CHAT_ID, type="supergroup"),
            text="hello",
        ),
    )

    assert len(recorder.messages) == 1


async def test_channel_post_reaches_the_handler(bot: Bot) -> None:
    recorder = _Recorder()
    dp = _dispatcher(recorder, AlbumMiddleware(latency=0.01))

    await _feed(dp, bot, _channel_post())

    assert len(recorder.messages) == 1


async def test_start_command_is_ignored_in_private_chat(bot: Bot) -> None:
    recorder = _Recorder()
    dp = _dispatcher(recorder, AlbumMiddleware(latency=0.01))

    await _feed(dp, bot, _message(chat_id=USER_ID, chat_type="private", text="/start"))

    assert recorder.starts == 0
    assert recorder.messages == []


def _photo_album(*, user_id: int, count: int = 3) -> list[Message]:
    photo = [PhotoSize(file_id="f", file_unique_id="u", width=1, height=1)]
    return [
        _message(user_id=user_id, message_id=i, media_group_id="group", photo=photo)
        for i in range(1, count + 1)
    ]


async def test_album_of_the_allowed_user_is_delivered_once(bot: Bot) -> None:
    recorder = _Recorder()
    dp = _dispatcher(recorder, AlbumMiddleware(latency=0.05))

    await _feed(dp, bot, *_photo_album(user_id=USER_ID))

    assert len(recorder.messages) == 1
    assert recorder.albums[0] is not None
    assert len(recorder.albums[0]) == 3


async def test_album_of_a_stranger_never_reaches_album_middleware(bot: Bot) -> None:
    recorder = _Recorder()
    album = _SpyAlbum(latency=0.05)
    dp = _dispatcher(recorder, album)

    await _feed(dp, bot, *_photo_album(user_id=STRANGER_ID))

    assert recorder.messages == []
    assert album.calls == 0


async def test_album_middleware_still_runs_for_the_allowed_user(bot: Bot) -> None:
    recorder = _Recorder()
    album = _SpyAlbum(latency=0.05)
    dp = _dispatcher(recorder, album)

    await _feed(dp, bot, *_photo_album(user_id=USER_ID))

    assert album.calls == 3
