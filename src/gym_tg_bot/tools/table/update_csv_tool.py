from typing import cast

from gym_tg_bot.table_store import TableStore
from gym_tg_bot.tools.base import Tool, ToolContext


class UpdateTableTool(Tool):
    def __init__(self, store: TableStore) -> None:
        self._store = store

    @property
    def definition(self) -> dict[str, object]:
        return {
            "type": "function",
            "function": {
                "name": "update_table",
                "description": (
                    "Replace the whole content of the user's existing csv table. "
                    "To add, change or remove rows, first read the table, then pass its "
                    "full new content, including the header and unchanged rows."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Name of the table to update. E.g. 'cutting_ration'.",
                        },
                        "content": {
                            "type": "array",
                            "description": (
                                "New table rows. The first row is the header. "
                                "Each row is a list of cell values. "
                                "Example: [['meal','weight (g)','protein','fat',"
                                "'carbs','calories'],['chicken','100','20','4','0','96']]."
                            ),
                            "items": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                    },
                    "required": ["table_name", "content"],
                },
            },
        }

    async def __call__(self, arguments: dict[str, object], context: ToolContext) -> str:
        try:
            self._store.update_table(
                chat_id=context.chat_id,
                table_name=str(arguments["table_name"]),
                content=cast(list[list[object]], arguments["content"]),
            )
        except (FileNotFoundError, ValueError) as e:
            return str(e)
        return "OK"
