import uuid

from gym_tg_bot.embeddings import Embedder
from gym_tg_bot.llm import LLMClient
from gym_tg_bot.memory import ThreadMemory
from gym_tg_bot.vector_store import VectorStore


class PostService:
    def __init__(
        self,
        llm: LLMClient,
        memory: ThreadMemory,
        embedder: Embedder,
        vector_store: VectorStore,
    ) -> None:
        self._llm = llm
        self._memory = memory
        self._embedder = embedder
        self._vector_store = vector_store

    async def respond(self, chat_id: int, thread_id: int, text: str, system_prompt: str) -> str:
        self._memory.add(chat_id, thread_id, "user", text)
        history = self._memory.get(chat_id, thread_id)

        answer = await self._llm.chat(system=system_prompt, messages=history)
        self._memory.add(chat_id, thread_id, "assistant", answer)
        return answer

    async def ingest(self, chat_id: int, message_id: int, text: str) -> None:
        vector = await self._embedder.embed(text)
        point_id = str(uuid.uuid5(uuid.NAMESPACE_OID, f"{chat_id}:{message_id}"))
        await self._vector_store.upsert_post(
            point_id=point_id,
            vector=vector,
            payload={"chat_id": chat_id, "message_id": message_id, "text": text},
        )
