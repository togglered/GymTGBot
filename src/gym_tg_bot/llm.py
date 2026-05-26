from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam


class LLMClient:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def chat(self, system: str, messages: list[ChatCompletionMessageParam]) -> str:
        api_messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system},
            *messages,
        ]
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=api_messages,
        )
        content = response.choices[0].message.content
        if content is None:
            raise RuntimeError("Empty response from LLM")
        return content
