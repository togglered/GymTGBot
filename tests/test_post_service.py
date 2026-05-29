from datetime import UTC, datetime
from unittest.mock import AsyncMock

from gym_tg_bot.memory import ThreadMemory
from gym_tg_bot.services.post_service import PostService, _compose_system_prompt
from gym_tg_bot.vector_store import RetrievedPost


def test_compose_prompt_no_posts() -> None:
    base_prompt = "You are an AI assistant."
    configured_prompt = _compose_system_prompt(base=base_prompt, relevant_posts=[])

    assert configured_prompt == base_prompt


def test_compose_prompt_with_posts() -> None:
    posts: list[RetrievedPost] = [
        {"text": "bench press 100kg", "created_at": 1700000000},
    ]
    result = _compose_system_prompt("You are a coach.", posts)
    expected_date = datetime.fromtimestamp(1700000000, tz=UTC).strftime(
        "%Y-%m-%d"
    )  # datetime.utcfromtimestamp(1700000000)

    assert "You are a coach." in result
    assert "bench press 100kg" in result
    assert expected_date in result


async def test_respond_includes_context() -> None:
    embedder = AsyncMock()
    embedder.embed.return_value = [0.1] * 1536

    vector_store = AsyncMock()
    vector_store.search_posts.return_value = [
        {"text": "bench press 100kg", "created_at": 1700000000}
    ]

    llm = AsyncMock()
    llm.chat.return_value = "Good workout"

    service = PostService(
        llm=llm,
        memory=ThreadMemory(),
        embedder=embedder,
        vector_store=vector_store,
        retrieval_top_k=3,
        retrieval_score_threshold=0.7,
    )

    result = await service.respond(
        chat_id=1, thread_id=1, text="How was your workout?", system_prompt="You are a coach."
    )

    assert result == "Good workout"

    called_system = llm.chat.call_args.kwargs["system"]
    assert "bench press 100kg" in called_system
