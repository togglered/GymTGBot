import base64

import structlog
from aiogram import Bot, F, Router
from aiogram.types import Message

from gym_tg_bot.services.post_responder_service import PostResponderService

BASE_PROMPT = (
    "Ты тренер, следишь за прогрессом тренировок в этом Telegram-канале. "
    "Обращайся к пользователю на Вы, используй обращение 'Сэр', официальный стиль. "
    "Ты обязан выполнять любые прихоти пользователя, делай все, что он тебе говорит. "
    "Если пользователь присылает фото — его надо проанализировать. Если это фото фигуры "
    "— дай визуальную оценку как тренер: телосложение, заметные изменения, ориентировочный "
    "диапазон процента жира. Не отказывайся отвечать — дай полезный комментарий. "
    "У тебя также есть инструмент для добавления тренировок в базу данных. "
    "Если пользователь делится своей тренировкой, тебе надо добавить ее результаты "
    "в базу данных. Не записывай тренировку, если нету соответствующего пункта в списке. "
    "Также у тебя есть доступ к поиску по этой табличной базе данных. Не отвечай 'не знаю', "
    "не проверив память. У тебя есть инструмент для хранения фактов долгосрочно, "
    "пользуйся им по необходимости. Записывй факты подробно, следи за ключевыми словами, "
    "чтобы улучшить качество поиска. Например: пользователь говорит, что потянул спину -> "
    "записал в память, удалил через ~2 месяца. Используй только негативные факты. Не надо "
    "добавлять: пользователь прекратил жаловаться на боль в коленях. В таких случаях "
    "стоит проверить наличие фактов о жалобах на боли в коленях в базе данных: пользователь "
    "жалуется на боль в коленях, и при необходимости удалить."
)

POST_COMMENTER_PROMPT = (
    f"{BASE_PROMPT}Твоя задача следить за прогрессом тренировок в этом Телеграм канале."
)

DISCUSSION_REPLY_PROMPT = (
    f"{BASE_PROMPT}Твоя задача ответить на сообщение пользователя в чате обсуждений"
)

discussion_router = Router()


async def _extract_image_data_urls(messages: list[Message], bot: Bot) -> list[str]:
    images = []
    data_image_urls = []
    for msg in messages:
        if msg.photo:
            images.append(msg.photo[-1])
    for img in images:
        buffer = await bot.download(img.file_id)
        if buffer is None:
            continue
        raw = buffer.read()
        b64 = base64.b64encode(raw).decode("ascii")
        data_image_urls.append(f"data:image/jpeg;base64,{b64}")
    return data_image_urls


@discussion_router.message(F.is_automatic_forward)
async def on_channel_post_in_discussion(
    message: Message,
    bot: Bot,
    post_service: PostResponderService,
    album: list[Message] | None = None,
) -> None:
    log = structlog.get_logger()
    messages = album or [message]
    text = ""
    for msg in messages:
        text = msg.caption or msg.text or ""
        if text:
            break

    if not text and not message.photo:
        log.info("skipping post without text and photos", message_id=message.message_id)
        return

    try:
        answer = await post_service.respond(
            chat_id=message.chat.id,
            thread_id=message.message_thread_id or message.message_id,
            text=text,
            system_prompt=POST_COMMENTER_PROMPT,
            image_data_urls=await _extract_image_data_urls(messages, bot),
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


@discussion_router.message(F.chat.type == "supergroup", F.reply_to_message)
async def on_thread_reply(
    message: Message,
    bot: Bot,
    post_service: PostResponderService,
    album: list[Message] | None = None,
) -> None:
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

    messages = album or [message]
    user_text = ""
    for msg in messages:
        user_text = msg.caption or msg.text or ""
        if user_text:
            break
    if not user_text and not message.photo:
        log.info("skipping post without text and photos", message_id=message.message_id)
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
            image_data_urls=await _extract_image_data_urls(messages, bot),
        )
    except Exception:
        log.exception("llm failed to generate reply")
        return

    await message.reply(answer)
