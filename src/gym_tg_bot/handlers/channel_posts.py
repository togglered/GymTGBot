import structlog
from aiogram import Router
from aiogram.types import Message

from gym_tg_bot.services.post_service import PostService

channel_posts_router = Router()


@channel_posts_router.channel_post()
async def on_channel_post(message: Message, post_service: PostService) -> None:
    log = structlog.get_logger()
    text = message.text or message.caption or ""

    if not text:
        log.info("skipping channel post without text", message_id=message.message_id)
        return

    try:
        await post_service.ingest(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=text,
        )
    except Exception:
        log.exception("failed to ingest channel post", message_id=message.message_id)
        return

    log.info("channel post ingested", message_id=message.message_id)
