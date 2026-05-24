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
