from pathlib import Path
from unittest.mock import AsyncMock

from gym_tg_bot.chat import ToolCall
from gym_tg_bot.memory import ThreadMemory
from gym_tg_bot.services.post_responder_service import PostResponderService


async def test_agent_loop_executes_tool_and_returns_final_answer(tmp_path: Path) -> None:
    memory = ThreadMemory(tmp_path / "test.db")
    await memory.ensure_schema()
    llm = AsyncMock()
    llm.chat_with_tools.side_effect = [
        [ToolCall(id="call_1", name="search_memory", arguments={"query": "bench"})],
        "A 100-kilogram bench press is good progress, sir",
    ]

    fake_tool = AsyncMock()
    fake_tool.definition = {
        "type": "function",
        "function": {"name": "search_memory", "description": "...", "parameters": {}},
    }
    fake_tool.return_value = "Result: 100 kg bench press"

    service = PostResponderService(llm=llm, memory=memory, tools=[fake_tool])

    result = await service.respond(
        chat_id=1,
        thread_id=1,
        text="How's my bench press coming along?",
        system_prompt="You're the coach",
    )

    assert result == "A 100-kilogram bench press is good progress, sir"
    assert llm.chat_with_tools.call_count == 2
    fake_tool.assert_called_once_with(query="bench")
