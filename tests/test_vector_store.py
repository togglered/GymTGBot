from pathlib import Path

import pytest

from gym_tg_bot.vector_store import VectorStore


@pytest.fixture
async def store(tmp_path: Path) -> VectorStore:
    store = VectorStore(path=tmp_path, vector_size=4)
    await store.ensure_collection()
    return store


async def test_search_returns_posts(store: VectorStore) -> None:
    await store.upsert_post(
        point_id="aaaaaaaa-0000-0000-0000-000000000001",
        vector=[1.0, 0.0, 0.0, 0.0],
        payload={"message_id": 1, "text": "bench press", "created_at": 1700000000},
    )

    results = await store.search_posts(vector=[1.0, 0.0, 0.0, 0.0], top_k=5, score_threshold=0.5)

    assert len(results) == 1
    assert results[0]["text"] == "bench press"


async def test_search_excludes_message_id(store: VectorStore) -> None:
    await store.upsert_post(
        point_id="aaaaaaaa-0000-0000-0000-000000000001",
        vector=[1.0, 0.0, 0.0, 0.0],
        payload={"message_id": 1, "text": "bench press", "created_at": 1700000000},
    )
    await store.upsert_post(
        point_id="aaaaaaaa-0000-0000-0000-000000000002",
        vector=[1.0, 0.0, 0.0, 0.0],
        payload={"message_id": 2, "text": "squat", "created_at": 1700000001},
    )

    results = await store.search_posts(
        vector=[1.0, 0.0, 0.0, 0.0], top_k=5, score_threshold=0.5, exclude_message_id=1
    )

    assert len(results) == 1
    assert results[0]["text"] == "squat"
