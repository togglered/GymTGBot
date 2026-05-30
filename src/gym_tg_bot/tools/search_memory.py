from datetime import UTC, datetime

from gym_tg_bot.embeddings import Embedder
from gym_tg_bot.tools.base import Tool
from gym_tg_bot.vector_store import VectorStore


class SearchMemoryTool(Tool):
    @property
    def definition(self) -> dict[str, object]:
        return {
            "type": "function",
            "function": {
                "name": "search_memory",
                "description": "Search for similar posts in the channel's long-term archive",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                    },
                    "required": ["query"],
                },
            },
        }

    def __init__(
        self,
        embedder: Embedder,
        vector_store: VectorStore,
        top_k: int,
        score_threshold: float,
    ) -> None:
        self._embedder = embedder
        self._vector_store = vector_store
        self._top_k = top_k
        self._score_threshold = score_threshold

    async def __call__(self, **kwargs: object) -> str:
        query = str(kwargs["query"])
        vector = await self._embedder.embed(query)
        posts = await self._vector_store.search_posts(
            vector=vector,
            top_k=self._top_k,
            score_threshold=self._score_threshold,
        )
        if not posts:
            return "No similar posts were found."
        lines = []
        for p in posts:
            date_str = datetime.fromtimestamp(p["created_at"], tz=UTC).strftime("%Y-%m-%d")
            lines.append(f"- [{date_str}] {p['text']}")
        return "\n".join(lines)
