import csv
import re
from pathlib import Path

_VALID_TABLE_NAME = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
_SCALAR_TYPES = (str, int, float, bool, type(None))


def _validate_content(content: object) -> None:
    if not isinstance(content, list):
        raise ValueError("Invalid table content: expected a list of rows.")
    for row_index, row in enumerate(content):
        if not isinstance(row, list):
            raise ValueError(
                f"Invalid table content: row {row_index} must be a list of cell values, "
                f"got {type(row).__name__}. Pass rows as a list of lists."
            )
        for cell_index, cell in enumerate(row):
            if not isinstance(cell, _SCALAR_TYPES):
                raise ValueError(
                    f"Invalid table content: cell {cell_index} in row {row_index} "
                    f"must be a string or a number, got {type(cell).__name__}."
                )


class TableStore:
    def __init__(self, folder_path: Path) -> None:
        self._folder_path = folder_path
        self._folder_path.mkdir(parents=True, exist_ok=True)

    def _convert_name_to_path(self, chat_id: int, table_name: str) -> Path:
        if not _VALID_TABLE_NAME.fullmatch(table_name):
            raise ValueError(
                f"Invalid table name: {table_name!r}. "
                "Allowed: letters, digits, '_' and '-', up to 64 chars."
            )
        return self._folder_path / str(chat_id) / f"{table_name}.csv"

    def read_table(self, chat_id: int, table_name: str) -> str:
        csv_path = self._convert_name_to_path(chat_id, table_name)
        if not csv_path.exists():
            raise FileNotFoundError(f"Table {table_name} wasn't found")
        return csv_path.read_text(encoding="utf-8")

    def create_table(self, chat_id: int, table_name: str, content: list[list[object]]) -> Path:
        csv_path = self._convert_name_to_path(chat_id, table_name)
        _validate_content(content)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        if csv_path.exists():
            raise FileExistsError(f"Table {table_name} already exists")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(content)
        return csv_path

    def update_table(self, chat_id: int, table_name: str, content: list[list[object]]) -> Path:
        csv_path = self._convert_name_to_path(chat_id, table_name)
        _validate_content(content)
        if not csv_path.exists():
            raise FileNotFoundError(f"Table {table_name} wasn't found")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(content)
        return csv_path

    def delete_table(self, chat_id: int, table_name: str) -> None:
        csv_path = self._convert_name_to_path(chat_id, table_name)
        if csv_path.exists():
            csv_path.unlink()
        else:
            raise FileNotFoundError(f"Table {table_name} wasn't found")

    def list_tables(self, chat_id: int) -> list[Path]:
        tables = []
        folder_path = self._folder_path / str(chat_id)
        if not folder_path.exists():
            return []
        for file in folder_path.iterdir():
            if file.suffix.lower() == ".csv":
                tables.append(file)
        return tables
