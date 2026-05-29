from typing import cast

from openai.types.chat import ChatCompletionMessageParam

from gym_tg_bot.llm import LLMClient
from gym_tg_bot.memory import ThreadMemory


class PostService:
    def __init__(self, llm: LLMClient, memory: ThreadMemory):
        self._llm = llm
        self._memory = memory

    async def respond(self, chat_id: int, thread_id: int, text: str, system_prompt: str) -> str:
        self._memory.add(chat_id, thread_id, "user", text)
        history = cast(
            list[ChatCompletionMessageParam],
            self._memory.get(chat_id, thread_id),
        )

        answer = await self._llm.chat(system=system_prompt, messages=history)
        self._memory.add(chat_id, thread_id, "assistant", answer)
        return answer
