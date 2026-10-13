from pathlib import Path
from typing import Any, cast

import pytest

from gym_tg_bot.table_store import TableStore
from gym_tg_bot.tools.base import ToolContext
from gym_tg_bot.tools.table.update_csv_tool import UpdateTableTool


@pytest.fixture
def store(tmp_path: Path) -> TableStore:
    return TableStore(tmp_path)


@pytest.fixture
def tool(store: TableStore) -> UpdateTableTool:
    return UpdateTableTool(store)


def test_definition(tool: UpdateTableTool) -> None:
    definition = cast(dict[str, Any], tool.definition)
    assert definition["type"] == "function"
    assert definition["function"]["name"] == "update_table"
    parameters = definition["function"]["parameters"]
    assert set(parameters["required"]) == {"table_name", "content"}
    assert set(parameters["properties"]) == {"table_name", "content"}


@pytest.mark.asyncio
async def test_update_table(tool: UpdateTableTool, store: TableStore) -> None:
    store.create_table(123, "diet", [["meal", "protein"], ["chicken", "20"]])

    result = await tool(
        {
            "table_name": "diet",
            "content": [["meal", "protein"], ["chicken", "20"], ["rice", "7"]],
        },
        ToolContext(chat_id=123),
    )
    assert result == "OK"
    assert store.read_table(123, "diet") == "meal,protein\nchicken,20\nrice,7\n"


@pytest.mark.asyncio
async def test_update_not_existing_table(tool: UpdateTableTool, store: TableStore) -> None:
    result = await tool(
        {"table_name": "diet", "content": [["meal"], ["chicken"]]},
        ToolContext(chat_id=123),
    )
    assert result == "Table diet wasn't found"
    assert store.list_tables(123) == []


@pytest.mark.asyncio
async def test_invalid_table_name(tool: UpdateTableTool) -> None:
    result = await tool(
        {"table_name": "../etc", "content": [["meal"]]},
        ToolContext(chat_id=123),
    )
    assert "Invalid table name" in result


@pytest.mark.asyncio
async def test_isolation_between_chats(tool: UpdateTableTool, store: TableStore) -> None:
    store.create_table(1, "diet", [["chicken"]])
    store.create_table(2, "diet", [["rice"]])

    assert await tool({"table_name": "diet", "content": [["beef"]]}, ToolContext(chat_id=1)) == "OK"
    assert store.read_table(1, "diet") == "beef\n"
    assert store.read_table(2, "diet") == "rice\n"
