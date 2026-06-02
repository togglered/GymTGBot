from pathlib import Path

import pytest

from gym_tg_bot.chat import ChatMessage, ImagePart, TextPart, ToolCall, ToolResult
from gym_tg_bot.memory import ThreadMemory


@pytest.fixture
async def mem(tmp_path: Path) -> ThreadMemory:
    memory = ThreadMemory(tmp_path / "test.db")
    await memory.ensure_schema()
    return memory


@pytest.mark.asyncio
async def test_chat_message_round_trip(mem: ThreadMemory) -> None:
    msg = ChatMessage(role="user", content="hello")
    await mem.add(chat_id=1, thread_id=10, item=msg)

    assert await mem.get(1, 10) == [msg]


@pytest.mark.asyncio
async def test_tool_call_round_trip(mem: ThreadMemory) -> None:
    msg = ToolCall(
        id="12345",
        name="search_memory",
        arguments={"query": "squat"},
    )
    await mem.add(chat_id=2, thread_id=13, item=msg)

    assert await mem.get(2, 13) == [msg]


@pytest.mark.asyncio
async def test_tool_result_round_trip(mem: ThreadMemory) -> None:
    msg = ToolResult(tool_call_id="12345", content="Nothing found.")
    await mem.add(chat_id=2, thread_id=13, item=msg)

    assert await mem.get(2, 13) == [msg]


@pytest.mark.asyncio
async def test_thread_isolation(mem: ThreadMemory) -> None:
    msg1 = ChatMessage(role="user", content="hi!")
    await mem.add(chat_id=1, thread_id=15, item=msg1)
    msg2 = ChatMessage(role="user", content="hello")
    await mem.add(chat_id=1, thread_id=20, item=msg2)

    assert await mem.get(1, 15) == [msg1]
    assert await mem.get(1, 20) == [msg2]


@pytest.mark.asyncio
async def test_chat_isolation(mem: ThreadMemory) -> None:
    """
    Different chats, same thread_id's
    """
    msg1 = ChatMessage(role="user", content="hi!")
    await mem.add(chat_id=1, thread_id=15, item=msg1)
    msg2 = ChatMessage(role="user", content="hello")
    await mem.add(chat_id=2, thread_id=15, item=msg2)

    assert await mem.get(1, 15) == [msg1]
    assert await mem.get(2, 15) == [msg2]


@pytest.mark.asyncio
async def test_empty_thread(mem: ThreadMemory) -> None:
    await mem.add(chat_id=1, thread_id=15, item=ChatMessage(role="user", content="hi!"))

    assert await mem.get(1, 20) == []


@pytest.mark.asyncio
async def test_mixed_order(mem: ThreadMemory) -> None:
    msgs: list[ChatMessage | ToolCall | ToolResult] = [
        ChatMessage(role="user", content="hi!"),
        ToolResult(tool_call_id="12345", content="Nothing found."),
        ToolCall(
            id="12345",
            name="search_memory",
            arguments={"query": "squat"},
        ),
        ChatMessage(role="user", content="okey"),
    ]
    for msg in msgs:
        await mem.add(chat_id=1, thread_id=15, item=msg)

    assert await mem.get(1, 15) == msgs


@pytest.mark.asyncio
async def test_type_image(mem: ThreadMemory) -> None:
    item = ChatMessage(
        role="user",
        content=[
            TextPart(text="What do you see on this photo?"),
            ImagePart(image_url="data:image/jpeg;base64,AAA"),
        ],
    )
    await mem.add(chat_id=1, thread_id=1, item=item)
    msgs = await mem.get(1, 1)
    assert msgs == [item]


@pytest.mark.asyncio
async def test_role_check(mem: ThreadMemory) -> None:
    user_msg = ChatMessage(role="user", content="What time is now?")
    ai_msg = ChatMessage(role="assistant", content="16:00")
    await mem.add(chat_id=1, thread_id=1, item=user_msg)
    await mem.add(chat_id=1, thread_id=1, item=ai_msg)

    msgs = await mem.get(1, 1)
    first, second = msgs[0], msgs[1]
    assert isinstance(first, ChatMessage)
    assert isinstance(second, ChatMessage)
    assert first.role == "user"
    assert second.role == "assistant"
