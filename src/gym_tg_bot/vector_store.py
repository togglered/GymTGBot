from pathlib import Path

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

_COLLECTION = "channel_posts"


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
