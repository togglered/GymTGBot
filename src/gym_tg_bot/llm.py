from typing import Protocol

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from gym_tg_bot.chat import ChatMessage


class LLMClient(Protocol):
    async def chat(self, system: str, messages: list[ChatMessage]) -> str: ...


class OpenAILLMClient:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def chat(self, system: str, messages: list[ChatMessage]) -> str:
        api_messages: list[ChatCompletionMessageParam] = [{"role": "system", "content": system}]
        for msg in messages:
            if msg["role"] == "user":
                api_messages.append({"role": "user", "content": msg["content"]})
            else:
                api_messages.append({"role": "assistant", "content": msg["content"]})
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=api_messages,
        )
        content = response.choices[0].message.content
        if content is None:
            raise RuntimeError("Empty response from LLM")
        return content
