from pathlib import Path
from typing import TypedDict

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

_COLLECTION = "channel_posts"


class RetrievedPost(TypedDict):
    text: str
    created_at: int


class VectorStore:
    def __init__(self, path: Path, vector_size: int) -> None:
        self._client = AsyncQdrantClient(path=str(path))
        self._vector_size = vector_size

    async def ensure_collection(self) -> None:
        exists = await self._client.collection_exists(_COLLECTION)
        if not exists:
            await self._client.create_collection(
                collection_name=_COLLECTION,
                vectors_config=VectorParams(
                    size=self._vector_size,
                    distance=Distance.COSINE,
                ),
            )

    async def upsert_post(
        self, point_id: str, vector: list[float], payload: dict[str, object]
    ) -> None:
        await self._client.upsert(
            collection_name=_COLLECTION,
            points=[PointStruct(id=point_id, vector=vector, payload=payload)],
        )

    async def search_posts(
        self,
        vector: list[float],
        top_k: int,
        score_threshold: float,
        exclude_message_id: int | None = None,
    ) -> list[RetrievedPost]:
        query_filter = None
        if exclude_message_id is not None:
            query_filter = Filter(
                must_not=[
                    FieldCondition(
                        key="message_id",
                        match=MatchValue(value=exclude_message_id),
                    )
                ]
            )
        response = await self._client.query_points(
            collection_name=_COLLECTION,
            query=vector,
            limit=top_k,
            score_threshold=score_threshold,
            with_payload=True,
            query_filter=query_filter,
        )
        posts: list[RetrievedPost] = []
        for point in response.points:
            if not point.payload:
                continue
            posts.append(
                {
                    "text": str(point.payload.get("text", "")),
                    "created_at": int(point.payload.get("created_at", 0)),
                }
            )
        return posts
