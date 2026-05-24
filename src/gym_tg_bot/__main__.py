import asyncio

import structlog
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from gym_tg_bot.config import Settings
from gym_tg_bot.llm import LLMClient
from gym_tg_bot.logging import configure_logging

POST_COMMENTER_PROMPT = (
    "Ты дружелюбный участник чата обсуждений Telegram-канала.Напиши комментарий к посту"
)

DISCUSSION_REPLY_PROMPT = (
    "Ты участник чата обсуждений Telegram-канала. "
    "Вам показывают предыдущее сообщение (пост канала или твой прошлый ответ) "
    "и реплику пользователя. Ответь по существу, 1-3 предложения, без эмодзи."
)

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer("Hi!")


@router.message(F.is_automatic_forward)
async def on_channel_post_in_discussion(message: Message, llm: LLMClient) -> None:
    log = structlog.get_logger()
    text = message.text or message.caption or ""

    if not text:
        log.info("skipping post without text", message_id=message.message_id)
        return

    log.info("channel post received", message_id=message.message_id, text_preview=text[:80])

    try:
        comment = await llm.ask(system=POST_COMMENTER_PROMPT, user=text)
    except Exception:
        log.exception("llm failed to generate comment")
        return

    await message.reply(comment)


@router.message(F.chat.type == "supergroup", F.reply_to_message)
async def on_thread_reply(message: Message, bot: Bot, llm: LLMClient) -> None:
    log = structlog.get_logger()
    reply_to = message.reply_to_message
    if reply_to is None:
        return

    bot_user = await bot.me()
    reply_to_user = reply_to.from_user

    addresses_bot = reply_to.is_automatic_forward or (
        reply_to_user is not None and reply_to_user.id == bot_user.id
    )
    if not addresses_bot:
        log.debug(
            "ignoring side conversation",
            chat_id=message.chat.id,
            message_id=message.message_id,
        )
        return

    user_text = message.text or message.caption or ""
    if not user_text:
        log.info("skipping non-text reply", message_id=message.message_id)
        return

    context_text = reply_to.text or reply_to.caption or ""

    log.info(
        "thread reply addressed to bot",
        chat_id=message.chat.id,
        user_id=message.from_user.id if message.from_user else None,
        replied_to_bot=not reply_to.is_automatic_forward,
        text_preview=user_text[:80],
    )

    prompt = f"Context:{context_text}\nUser's message:{user_text}"

    try:
        answer = await llm.ask(system=DISCUSSION_REPLY_PROMPT, user=prompt)
    except Exception:
        log.exception("llm failed to generate reply")
        return

    await message.reply(answer)


async def main() -> None:
    settings = Settings()  # type: ignore[call-arg]
    configure_logging(settings.log_level)
    log = structlog.get_logger()

    bot = Bot(token=settings.bot_token.get_secret_value())
    llm = LLMClient(
        api_key=settings.openai_api_key.get_secret_value(),
        model=settings.openai_model,
    )

    dp = Dispatcher()
    dp["llm"] = llm
    dp.include_router(router)

    log.info("bot starting")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        log.info("bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
