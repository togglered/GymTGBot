from typing import cast

from gym_tg_bot.table_store import TableStore
from gym_tg_bot.tools.base import Tool, ToolContext


class CreateTableTool(Tool):
    def __init__(self, store: TableStore) -> None:
        self._store = store

    @property
    def definition(self) -> dict[str, object]:
        return {
            "type": "function",
            "function": {
                "name": "create_table",
                "description": "Create a csv table",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "New table's name. E.g. 'cutting_ration'.",
                        },
                        "content": {
                            "type": "array",
                            "description": (
                                "Table rows. The first row is the header. "
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
            self._store.create_table(
                chat_id=context.chat_id,
                table_name=str(arguments["table_name"]),
                content=cast(list[list[object]], arguments["content"]),
            )
        except (FileExistsError, ValueError) as e:
            return str(e)
        return "OK"
