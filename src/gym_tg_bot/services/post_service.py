import uuid
from datetime import UTC, datetime

from gym_tg_bot.embeddings import Embedder
from gym_tg_bot.llm import LLMClient
from gym_tg_bot.memory import ThreadMemory
from gym_tg_bot.vector_store import RetrievedPost, VectorStore


def _compose_system_prompt(base: str, relevant_posts: list[RetrievedPost]) -> str:
    if not relevant_posts:
        return base
    lines = []
    for post in relevant_posts:
        date_str = datetime.fromtimestamp(post["created_at"], tz=UTC).strftime("%Y-%m-%d")
        lines.append(f"- [{date_str}] {post['text']}")
    context = "\n".join(lines)
    return f"{base}\n\nКонтекст из похожих постов канала:\n{context}"


class PostService:
    def __init__(
        self,
        llm: LLMClient,
        memory: ThreadMemory,
        embedder: Embedder,
        vector_store: VectorStore,
        retrieval_top_k: int,
        retrieval_score_threshold: float,
    ) -> None:
        self._llm = llm
        self._memory = memory
        self._embedder = embedder
        self._vector_store = vector_store
        self._retrieval_top_k = retrieval_top_k
        self._retrieval_score_threshold = retrieval_score_threshold

    async def respond(
        self,
        chat_id: int,
        thread_id: int,
        text: str,
        system_prompt: str,
        exclude_message_id: int | None = None,
    ) -> str:
        self._memory.add(chat_id, thread_id, "user", text)
        history = self._memory.get(chat_id, thread_id)

        query_vector = await self._embedder.embed(text)
        relevant_posts = await self._vector_store.search_posts(
            vector=query_vector,
            top_k=self._retrieval_top_k,
            score_threshold=self._retrieval_score_threshold,
            exclude_message_id=exclude_message_id,
        )
        full_system_prompt = _compose_system_prompt(system_prompt, relevant_posts)

        answer = await self._llm.chat(system=full_system_prompt, messages=history)
        self._memory.add(chat_id, thread_id, "assistant", answer)
        return answer

    async def ingest(
        self,
        chat_id: int,
        message_id: int,
        text: str,
        created_at: int,
    ) -> None:
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
