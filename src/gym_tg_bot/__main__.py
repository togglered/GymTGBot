import asyncio

import structlog
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from gym_tg_bot.config import Settings
from gym_tg_bot.logging import configure_logging

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer("Hi!")


@router.message(F.is_automatic_forward)
async def on_channel_post_in_discussion(message: Message) -> None:
    log = structlog.get_logger()
    text = message.text or message.caption or ""

    log.info(
        "channel post received",
        chat_id=message.chat.id,
        chat_title=message.chat.title,
        original_chat_id=message.forward_from_chat.id if message.forward_from_chat else None,
        message_id=message.message_id,
        text_preview=text[:80],
    )

    await message.reply(f"Echo: {text[:100]}")


@router.message(F.chat.type == "supergroup", F.reply_to_message)
async def on_thread_reply(message: Message, bot: Bot) -> None:
    log = structlog.get_logger()
    reply_to = message.reply_to_message
    if reply_to is None:
        return

    bot_user = await bot.me()
    reply_to_user = reply_to.from_user

    addresses_bot = (
        reply_to.is_automatic_forward  # original post reply
        or (reply_to_user is not None and reply_to_user.id == bot_user.id)  # bots reply
    )

    if not addresses_bot:
        log.debug(
            "ignoring side conversation in thread",
            chat_id=message.chat.id,
            message_id=message.message_id,
        )
        return

    user_id = message.from_user.id if message.from_user else None
    text = message.text or message.caption or "<media>"

    log.info(
        "thread reply addressed to bot",
        chat_id=message.chat.id,
        user_id=user_id,
        reply_to_message_id=reply_to.message_id,
        replied_to_bot=not reply_to.is_automatic_forward,
        text_preview=text[:80],
    )

    await message.reply("Message received.")


async def main() -> None:
    settings = Settings()  # type: ignore[call-arg]  # bot_token comes from env
    configure_logging(settings.log_level)
    log = structlog.get_logger()

    bot = Bot(token=settings.bot_token.get_secret_value())
    dp = Dispatcher()
    dp.include_router(router)

    log.info("bot starting")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        log.info("bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
