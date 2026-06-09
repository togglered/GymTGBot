from datetime import UTC, datetime

from gym_tg_bot.embeddings import Embedder
from gym_tg_bot.tools.base import Tool, ToolContext
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

    async def __call__(self, arguments: dict[str, object], context: ToolContext) -> str:
        query = str(arguments["query"])
        vector = await self._embedder.embed(query)
        posts = await self._vector_store.search_posts(
            chat_id=context.chat_id,
            vector=vector,
            top_k=self._top_k,
            score_threshold=self._score_threshold,
        )
        if not posts:
            return "No similar posts were found."
        posts.sort(key=lambda p: p["created_at"], reverse=True)
        lines = []
        for p in posts:
            date_str = datetime.fromtimestamp(p["created_at"], tz=UTC).strftime("%Y-%m-%d")
            lines.append(f"- [{date_str}] {p['text']}")
        return "\n".join(lines)
