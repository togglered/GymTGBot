from gym_tg_bot.table_store import TableStore
from gym_tg_bot.tools.base import Tool, ToolContext


class DeleteTableTool(Tool):
    def __init__(self, store: TableStore) -> None:
        self._store = store

    @property
    def definition(self) -> dict[str, object]:
        return {
            "type": "function",
            "function": {
                "name": "delete_table",
                "description": "Delete the user's csv table",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Name of the table to delete. E.g. 'cutting_ration'.",
                        },
                    },
                    "required": ["table_name"],
                },
            },
        }

    async def __call__(self, arguments: dict[str, object], context: ToolContext) -> str:
        try:
            self._store.delete_table(
                chat_id=context.chat_id,
                table_name=str(arguments["table_name"]),
            )
        except (FileNotFoundError, ValueError) as e:
            return str(e)
        return "OK"
