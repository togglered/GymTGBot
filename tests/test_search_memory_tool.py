from unittest.mock import AsyncMock

from gym_tg_bot.tools.base import ToolContext
from gym_tg_bot.tools.search_memory import SearchMemoryTool


async def test_returns_formatted_posts() -> None:
    embedder = AsyncMock()
    embedder.embed.return_value = [0.1] * 1536

    vector_store = AsyncMock()
    vector_store.search_posts.return_value = [
        {"text": "bench press 100kg", "created_at": 1700000000},
    ]

    tool = SearchMemoryTool(embedder, vector_store, top_k=3, score_threshold=0.7)
    result = await tool({"query": "bench"}, ToolContext(chat_id=123))

    assert "bench press 100kg" in result
    assert "2023-11-14" in result


async def test_returns_message_when_no_posts() -> None:
    embedder = AsyncMock()
    embedder.embed.return_value = [0.1] * 1536

    vector_store = AsyncMock()
    vector_store.search_posts.return_value = []

    tool = SearchMemoryTool(embedder, vector_store, top_k=3, score_threshold=0.7)
    result = await tool({"query": "bench"}, ToolContext(chat_id=123))

    assert "No similar posts were found" in result


async def test_returns_posts_newest_first() -> None:
    embedder = AsyncMock()
    embedder.embed.return_value = [0.1] * 1536

    vector_store = AsyncMock()
    vector_store.search_posts.return_value = [
        {"text": "bench press 80kg", "created_at": 1500000000},
        {"text": "bench press 100kg", "created_at": 1700000000},
        {"text": "bench press 90kg", "created_at": 1600000000},
    ]

    tool = SearchMemoryTool(embedder, vector_store, top_k=3, score_threshold=0.7)
    result = await tool({"query": "bench"}, ToolContext(chat_id=123))

    assert result.index("80kg") > result.index("90kg") > result.index("100kg")
