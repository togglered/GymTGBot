import structlog
from aiogram import Bot, F, Router
from aiogram.types import Message

from gym_tg_bot.services.post_ingest_service import PostIngestService
from gym_tg_bot.services.post_responder_service import PostResponderService

BASE_PROMPT = (
    "Ты тренер, следишь за прогрессом тренировок в этом Telegram-канале. "
    "Обращайся к пользователю на Вы, используй обращение 'Сэр', официальный стиль. "
    "У тебя есть инструмент search_memory — им ты можешь искать предыдущие посты канала "
    "по запросу. У тебя также есть инструмент для добавления тренировок в базу данных. "
    "Если пользователь делится своей тренировкой, тебе надо добавить ее результаты "
    "в базу данных. Не записывай тренировку, если нету соответствующего пункта в списке. "
    "Также у тебя есть доступ к поиску по этой табличной базе данных. Не отвечай 'не знаю', "
    "не проверив память."
)

POST_COMMENTER_PROMPT = (
    f"{BASE_PROMPT}Твоя задача следить за прогрессом тренировок в этом Телеграм канале."
)

DISCUSSION_REPLY_PROMPT = (
    f"{BASE_PROMPT}Твоя задача ответить на сообщение пользователя в чате обсуждений"
)

discussion_router = Router()


@discussion_router.message(F.is_automatic_forward)
async def on_channel_post_in_discussion(
    message: Message,
    post_service: PostResponderService,
    post_ingest_service: PostIngestService,
) -> None:
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

    fwd_chat = message.forward_from_chat
    fwd_message_id = message.forward_from_message_id
    fwd_date = message.forward_date
    if fwd_chat is None or fwd_message_id is None or fwd_date is None:
        log.info("skipping ingest, not a channel forward", message_id=message.message_id)
        return
    try:
        await post_ingest_service.ingest(
            chat_id=fwd_chat.id,
            message_id=fwd_message_id,
            text=text,
            created_at=int(fwd_date.timestamp()),
        )
        log.info("channel post ingested", message_id=fwd_message_id)
    except Exception:
        log.exception("failed to ingest channel post", message_id=fwd_message_id)


@discussion_router.message(F.chat.type == "supergroup", F.reply_to_message)
async def on_thread_reply(message: Message, bot: Bot, post_service: PostResponderService) -> None:
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
