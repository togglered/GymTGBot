from pathlib import Path
from typing import Any, cast

import pytest

from gym_tg_bot.table_store import TableStore
from gym_tg_bot.tools.base import ToolContext
from gym_tg_bot.tools.table.delete_csv_tool import DeleteTableTool


@pytest.fixture
def store(tmp_path: Path) -> TableStore:
    return TableStore(tmp_path)


@pytest.fixture
def tool(store: TableStore) -> DeleteTableTool:
    return DeleteTableTool(store)


def test_definition(tool: DeleteTableTool) -> None:
    definition = cast(dict[str, Any], tool.definition)
    assert definition["type"] == "function"
    assert definition["function"]["name"] == "delete_table"
    parameters = definition["function"]["parameters"]
    assert parameters["required"] == ["table_name"]
    assert set(parameters["properties"]) == {"table_name"}


@pytest.mark.asyncio
async def test_delete_table(tool: DeleteTableTool, store: TableStore) -> None:
    store.create_table(123, "diet", [["meal"], ["chicken"]])

    result = await tool({"table_name": "diet"}, ToolContext(chat_id=123))
    assert result == "OK"
    assert store.list_tables(123) == []


@pytest.mark.asyncio
async def test_delete_not_existing_table(tool: DeleteTableTool) -> None:
    result = await tool({"table_name": "diet"}, ToolContext(chat_id=123))
    assert result == "Table diet wasn't found"


@pytest.mark.asyncio
async def test_invalid_table_name(tool: DeleteTableTool) -> None:
    result = await tool({"table_name": "../etc"}, ToolContext(chat_id=123))
    assert "Invalid table name" in result


@pytest.mark.asyncio
async def test_isolation_between_chats(tool: DeleteTableTool, store: TableStore) -> None:
    store.create_table(1, "diet", [["chicken"]])
    store.create_table(2, "diet", [["rice"]])

    assert await tool({"table_name": "diet"}, ToolContext(chat_id=1)) == "OK"
    assert store.list_tables(1) == []
    assert store.read_table(2, "diet") == "rice\n"
