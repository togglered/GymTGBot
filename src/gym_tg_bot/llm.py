import json
from typing import Any, Protocol, cast

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall

from gym_tg_bot.chat import ChatMessage, ToolCall, ToolResult


class LLMClient(Protocol):
    async def chat(self, system: str, messages: list[ChatMessage]) -> str: ...

    async def chat_with_tools(
        self,
        system: str,
        messages: list[ChatMessage | ToolCall | ToolResult],
        tools: list[dict[str, object]],
    ) -> str | list[ToolCall]: ...


class OpenAILLMClient:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def chat(self, system: str, messages: list[ChatMessage]) -> str:
        api_messages: list[ChatCompletionMessageParam] = [{"role": "system", "content": system}]
        for msg in messages:
            if msg.role == "user":
                api_messages.append({"role": "user", "content": msg.content})
            else:
                api_messages.append({"role": "assistant", "content": msg.content})
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=api_messages,
        )
        content = response.choices[0].message.content
        if content is None:
            raise RuntimeError("Empty response from LLM")
        return content

    async def chat_with_tools(
        self,
        system: str,
        messages: list[ChatMessage | ToolCall | ToolResult],
        tools: list[dict[str, object]],
    ) -> str | list[ToolCall]:
        api_messages: list[Any] = [{"role": "system", "content": system}]
        for msg in messages:
            match msg:
                case ChatMessage():
                    api_messages.append({"role": msg.role, "content": msg.content})
                case ToolCall():
                    api_messages.append(
                        {
                            "role": "assistant",
                            "tool_calls": [
                                {
                                    "id": msg.id,
                                    "type": "function",
                                    "function": {
                                        "name": msg.name,
                                        "arguments": json.dumps(msg.arguments),
                                    },
                                }
                            ],
                        }
                    )
                case ToolResult():
                    api_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": msg.tool_call_id,
                            "content": msg.content,
                        }
                    )

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=api_messages,
            tools=cast(list[Any], tools),
        )

        choice = response.choices[0]

        if choice.finish_reason == "tool_calls":
            assert choice.message.tool_calls is not None
            result = []
            for tc in choice.message.tool_calls:
                if not isinstance(tc, ChatCompletionMessageToolCall):
                    continue
                result.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=json.loads(tc.function.arguments),
                    )
                )
            return result
        else:
            content = choice.message.content
            if content is None:
                raise RuntimeError("Empty response from LLM")
            return content
