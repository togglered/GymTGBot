from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest

from gym_tg_bot.chat import ChatMessage
from gym_tg_bot.llm import OpenAILLMClient


def _reply(text: str = "ok") -> SimpleNamespace:
    message = SimpleNamespace(content=text, tool_calls=None)
    return SimpleNamespace(choices=[SimpleNamespace(message=message, finish_reason="stop")])


def _client(reasoning_effort: str | None = None) -> tuple[OpenAILLMClient, AsyncMock]:
    client = OpenAILLMClient(api_key="test", model="test-model", reasoning_effort=reasoning_effort)
    create = AsyncMock(return_value=_reply())
    client._client.chat.completions.create = create  # type: ignore[method-assign]
    return client, create


async def _call_both(client: OpenAILLMClient) -> None:
    await client.chat("system", [ChatMessage("user", "hi")])
    await client.chat_with_tools("system", [ChatMessage("user", "hi")], tools=[])


@pytest.mark.asyncio
async def test_reasoning_effort_is_not_sent_by_default() -> None:
    client, create = _client()
    await _call_both(client)

    assert create.await_count == 2
    for call in create.await_args_list:
        assert "reasoning_effort" not in call.kwargs
        assert call.kwargs["model"] == "test-model"


@pytest.mark.asyncio
@pytest.mark.parametrize("value", ["none", "low", "high"])
async def test_reasoning_effort_is_sent_when_configured(value: str) -> None:
    client, create = _client(reasoning_effort=value)
    await _call_both(client)

    assert create.await_count == 2
    for call in create.await_args_list:
        assert call.kwargs["reasoning_effort"] == value


@pytest.mark.asyncio
async def test_empty_reasoning_effort_counts_as_unset() -> None:
    client, create = _client(reasoning_effort="")
    await _call_both(client)

    for call in create.await_args_list:
        assert "reasoning_effort" not in call.kwargs


@pytest.mark.asyncio
async def test_tools_are_still_sent_with_reasoning_effort() -> None:
    client, create = _client(reasoning_effort="none")
    tools: list[dict[str, Any]] = [{"type": "function", "function": {"name": "t"}}]
    result = await client.chat_with_tools("system", [ChatMessage("user", "hi")], tools=tools)

    assert result == "ok"
    kwargs = create.await_args.kwargs  # type: ignore[union-attr]
    assert kwargs["tools"] == tools
    assert kwargs["reasoning_effort"] == "none"
