from pathlib import Path
from typing import Any, cast

import pytest

from gym_tg_bot.table_store import TableStore
from gym_tg_bot.tools.base import ToolContext
from gym_tg_bot.tools.table.list_csv_tool import ListTablesTool


@pytest.fixture
def store(tmp_path: Path) -> TableStore:
    return TableStore(tmp_path)


@pytest.fixture
def tool(store: TableStore) -> ListTablesTool:
    return ListTablesTool(store)


def test_definition(tool: ListTablesTool) -> None:
    definition = cast(dict[str, Any], tool.definition)
    assert definition["type"] == "function"
    assert definition["function"]["name"] == "list_tables"
    parameters = definition["function"]["parameters"]
    assert parameters["required"] == []
    assert parameters["properties"] == {}


@pytest.mark.asyncio
async def test_no_tables(tool: ListTablesTool) -> None:
    result = await tool({}, ToolContext(chat_id=123))
    assert result == "No tables found"


@pytest.mark.asyncio
async def test_list_tables(tool: ListTablesTool, store: TableStore) -> None:
    store.create_table(123, "diet", [["meal"], ["chicken"]])
    store.create_table(123, "cutting", [["meal"], ["rice"]])

    result = await tool({}, ToolContext(chat_id=123))
    assert result == "cutting\ndiet"


@pytest.mark.asyncio
async def test_ignores_non_csv(tool: ListTablesTool, store: TableStore) -> None:
    store.create_table(123, "diet", [["meal"]])
    (store._folder_path / "123" / "file.txt").touch()

    result = await tool({}, ToolContext(chat_id=123))
    assert result == "diet"


@pytest.mark.asyncio
async def test_isolation_between_chats(tool: ListTablesTool, store: TableStore) -> None:
    store.create_table(1, "diet", [["chicken"]])
    store.create_table(2, "bulking", [["rice"]])

    assert await tool({}, ToolContext(chat_id=1)) == "diet"
    assert await tool({}, ToolContext(chat_id=2)) == "bulking"
