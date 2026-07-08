from pathlib import Path
from typing import Any, cast

import pytest

from gym_tg_bot.table_store import TableStore
from gym_tg_bot.tools.base import ToolContext
from gym_tg_bot.tools.table.create_csv_tool import CreateTableTool


@pytest.fixture
def store(tmp_path: Path) -> TableStore:
    return TableStore(tmp_path)


@pytest.fixture
def tool(store: TableStore) -> CreateTableTool:
    return CreateTableTool(store)


def test_definition(tool: CreateTableTool) -> None:
    definition = cast(dict[str, Any], tool.definition)
    assert definition["type"] == "function"
    assert definition["function"]["name"] == "create_table"
    parameters = definition["function"]["parameters"]
    assert set(parameters["required"]) == {"table_name", "content"}
    assert set(parameters["properties"]) == {"table_name", "content"}


@pytest.mark.asyncio
async def test_create_table(tool: CreateTableTool, store: TableStore) -> None:
    result = await tool(
        {
            "table_name": "diet",
            "content": [["meal", "protein", "fat", "carbs"], ["chicken", "20", "4", "0"]],
        },
        ToolContext(chat_id=123),
    )
    assert result == "OK"
    assert store.read_table(123, "diet") == "meal,protein,fat,carbs\nchicken,20,4,0\n"


@pytest.mark.asyncio
async def test_create_existing_table(tool: CreateTableTool) -> None:
    arguments: dict[str, object] = {"table_name": "diet", "content": [["meal"], ["chicken"]]}
    context = ToolContext(chat_id=123)
    assert await tool(arguments, context) == "OK"
    result = await tool(arguments, context)
    assert result == "Table diet already exists"


@pytest.mark.asyncio
async def test_invalid_table_name(tool: CreateTableTool, store: TableStore) -> None:
    result = await tool(
        {"table_name": "../etc", "content": [["meal"]]},
        ToolContext(chat_id=123),
    )
    assert "Invalid table name" in result
    assert store.list_tables(123) == []


@pytest.mark.asyncio
async def test_isolation_between_chats(tool: CreateTableTool, store: TableStore) -> None:
    assert await tool({"table_name": "diet", "content": [["chicken"]]}, ToolContext(chat_id=1))
    assert await tool({"table_name": "diet", "content": [["rice"]]}, ToolContext(chat_id=2))

    assert store.read_table(1, "diet") == "chicken\n"
    assert store.read_table(2, "diet") == "rice\n"
