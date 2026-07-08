from gym_tg_bot.table_store import TableStore
from gym_tg_bot.tools.base import Tool, ToolContext


class ListTablesTool(Tool):
    def __init__(self, store: TableStore) -> None:
        self._store = store

    @property
    def definition(self) -> dict[str, object]:
        return {
            "type": "function",
            "function": {
                "name": "list_tables",
                "description": "List names of the user's existing csv tables",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        }

    async def __call__(self, arguments: dict[str, object], context: ToolContext) -> str:
        tables = self._store.list_tables(context.chat_id)
        if not tables:
            return "No tables found"
        return "\n".join(sorted(table.stem for table in tables))
