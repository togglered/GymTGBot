import uuid

from gym_tg_bot.embeddings import Embedder
from gym_tg_bot.vector_store import VectorStore


class PostIngestService:
    def __init__(self, embedder: Embedder, vector_store: VectorStore) -> None:
        self._embedder = embedder
        self._vector_store = vector_store

    async def ingest(self, chat_id: int, message_id: int, text: str, created_at: int) -> None:
        vector = await self._embedder.embed(text)
        point_id = str(uuid.uuid5(uuid.NAMESPACE_OID, f"{chat_id}:{message_id}"))
        await self._vector_store.upsert_post(
            point_id=point_id,
            vector=vector,
            payload={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text,
                "created_at": created_at,
            },
        )
