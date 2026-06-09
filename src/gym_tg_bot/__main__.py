import asyncio

import structlog
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from gym_tg_bot.config import Settings
from gym_tg_bot.embeddings import OPENAI_EMBEDDING_SIZE, OpenAIEmbedder
from gym_tg_bot.handlers.discussion import discussion_router
from gym_tg_bot.llm import OpenAILLMClient
from gym_tg_bot.logging import configure_logging
from gym_tg_bot.memory import ThreadMemory
from gym_tg_bot.services.post_ingest_service import PostIngestService
from gym_tg_bot.services.post_responder_service import PostResponderService
from gym_tg_bot.tools.base import Tool
from gym_tg_bot.tools.search_memory import SearchMemoryTool
from gym_tg_bot.tools.workouts.add_workout import AddWorkoutTool
from gym_tg_bot.vector_store import VectorStore
from gym_tg_bot.workouts import WorkoutStore

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
    memory = ThreadMemory(settings.db_path)
    embedder = OpenAIEmbedder(
        api_key=settings.openai_api_key.get_secret_value(),
    )
    vector_store = VectorStore(path=settings.qdrant_path, vector_size=OPENAI_EMBEDDING_SIZE)
    workout_store = WorkoutStore(settings.db_path)

    await vector_store.ensure_collection()
    await workout_store.ensure_schema()
    await memory.ensure_schema()

    dp = Dispatcher()

    ingest_service = PostIngestService(embedder=embedder, vector_store=vector_store)
    tools: list[Tool] = [
        SearchMemoryTool(
            embedder,
            vector_store,
            top_k=settings.retrieval_top_k,
            score_threshold=settings.retrieval_score_threshold,
        ),
        AddWorkoutTool(workout_store),
    ]
    post_service = PostResponderService(llm=llm, memory=memory, tools=tools)

    dp["post_service"] = post_service
    dp["post_ingest_service"] = ingest_service

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
