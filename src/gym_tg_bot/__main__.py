import asyncio

import structlog
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from gym_tg_bot.config import Settings
from gym_tg_bot.handlers.discussion import discussion_router
from gym_tg_bot.llm import OpenAILLMClient
from gym_tg_bot.logging import configure_logging
from gym_tg_bot.memory import ThreadMemory
from gym_tg_bot.services.post_service import PostService

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer("Hi!")


async def main() -> None:
    settings = Settings()  # type: ignore[call-arg]
    configure_logging(settings.log_level)
    log = structlog.get_logger()

    bot = Bot(token=settings.bot_token.get_secret_value())
    llm = OpenAILLMClient(
        api_key=settings.openai_api_key.get_secret_value(),
        model=settings.openai_model,
    )
    memory = ThreadMemory()
    post_service = PostService(llm=llm, memory=memory)

    dp = Dispatcher()
    dp["post_service"] = post_service
    dp.include_router(router)
    dp.include_router(discussion_router)

    log.info("bot starting")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        log.info("bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
