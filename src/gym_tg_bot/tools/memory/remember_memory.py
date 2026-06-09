import time
import uuid

from gym_tg_bot.embeddings import Embedder
from gym_tg_bot.tools.base import Tool, ToolContext
from gym_tg_bot.vector_store import VectorStore


class RememberMemoryTool(Tool):
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

    @property
    def definition(self) -> dict[str, object]:
        return {
            "type": "function",
            "function": {
                "name": "remember_memory",
                "description": "Add important fact about user to the long-term memory",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": (
                                "Fact to remember. Must contain many key words to simplify search."
                            ),
                        },
                    },
                    "required": ["text"],
                },
            },
        }

    async def __call__(self, arguments: dict[str, object], context: ToolContext) -> str:
        text = str(arguments["text"])
        vector = await self._embedder.embed(text)
        await self._vector_store.upsert_post(
            point_id=str(uuid.uuid4()),
            vector=vector,
            payload={"chat_id": context.chat_id, "text": text, "created_at": int(time.time())},
        )
        return "The fact has been remembered"
