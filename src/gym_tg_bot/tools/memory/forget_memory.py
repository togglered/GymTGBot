from gym_tg_bot.embeddings import Embedder
from gym_tg_bot.tools.base import Tool, ToolContext
from gym_tg_bot.vector_store import VectorStore


class ForgetMemoryTool(Tool):
    def __init__(
        self,
        embedder: Embedder,
        vector_store: VectorStore,
        score_threshold: float,
    ) -> None:
        self._embedder = embedder
        self._vector_store = vector_store
        self._score_threshold = score_threshold

    @property
    def definition(self) -> dict[str, object]:
        return {
            "type": "function",
            "function": {
                "name": "forget_memory",
                "description": "Forget outdated fact in long-term memory",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Fact in long-term memory to forget",
                        },
                    },
                    "required": ["query"],
                },
            },
        }

    async def __call__(self, arguments: dict[str, object], context: ToolContext) -> str:
        query = str(arguments["query"])
        vector = await self._embedder.embed(query)
        memories = await self._vector_store.search_posts(
            chat_id=context.chat_id,
            vector=vector,
            top_k=1,
            score_threshold=self._score_threshold,
        )
        if not memories:
            return "Similar memories weren't found"
        await self._vector_store.delete_memory(memories[0]["id"])
        return f"Memory '{memories[0]['text']}' has been deleted"
