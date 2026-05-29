import structlog
from aiogram import Bot, F, Router
from aiogram.types import Message

from gym_tg_bot.services.post_service import PostService

POST_COMMENTER_PROMPT = (
    "Ты дружелюбный участник чата обсуждений Telegram-канала. Напиши комментарий к посту"
)

DISCUSSION_REPLY_PROMPT = (
    "Ты участник чата обсуждений Telegram-канала. "
    "Поддерживай разговор в треде. Ответь по существу, "
    "1-3 предложения, без эмодзи."
)

discussion_router = Router()


@discussion_router.message(F.is_automatic_forward)
async def on_channel_post_in_discussion(message: Message, post_service: PostService) -> None:
    log = structlog.get_logger()
    text = message.text or message.caption or ""

    if not text:
        log.info("skipping post without text", message_id=message.message_id)
        return

    try:
        answer = await post_service.respond(
            chat_id=message.chat.id,
            thread_id=message.message_thread_id or message.message_id,
            text=text,
            system_prompt=POST_COMMENTER_PROMPT,
        )
    except Exception:
        log.exception("llm failed to generate comment")
        return

    await message.reply(answer)


@discussion_router.message(F.chat.type == "supergroup", F.reply_to_message)
async def on_thread_reply(message: Message, bot: Bot, post_service: PostService) -> None:
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

    log.info(
        "thread reply addressed to bot",
        chat_id=message.chat.id,
        user_id=message.from_user.id if message.from_user else None,
        replied_to_bot=not reply_to.is_automatic_forward,
        text_preview=user_text[:80],
    )

    try:
        answer = await post_service.respond(
            chat_id=message.chat.id,
            thread_id=message.message_thread_id or message.message_id,
            text=user_text,
            system_prompt=DISCUSSION_REPLY_PROMPT,
        )
    except Exception:
        log.exception("llm failed to generate reply")
        return

    await message.reply(answer)
