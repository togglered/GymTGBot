import csv
import re
from pathlib import Path

_VALID_TABLE_NAME = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


class TableStore:
    def __init__(self, folder_path: Path) -> None:
        self._folder_path = folder_path
        self._folder_path.mkdir(parents=True, exist_ok=True)

    def _convert_name_to_path(self, table_name: str) -> Path:
        if not _VALID_TABLE_NAME.fullmatch(table_name):
            raise ValueError(
                f"Invalid table name: {table_name!r}. "
                "Allowed: letters, digits, '_' and '-', up to 64 chars."
            )
        return self._folder_path / f"{table_name}.csv"

    def read_table(self, table_name: str) -> str:
        csv_path = self._convert_name_to_path(table_name)
        if not csv_path.exists():
            raise FileNotFoundError(f"Table {table_name} wasn't found")
        return csv_path.read_text(encoding="utf-8")

    def create_table(self, table_name: str, content: list[list[object]]) -> Path:
        csv_path = self._convert_name_to_path(table_name)
        if csv_path.exists():
            raise FileExistsError(f"Table {table_name} already exists")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(content)
        return csv_path

    def update_table(self, table_name: str, content: list[list[object]]) -> Path:
        csv_path = self._convert_name_to_path(table_name)
        if not csv_path.exists():
            raise FileNotFoundError(f"Table {table_name} wasn't found")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(content)
        return csv_path

    def delete_table(self, table_name: str) -> None:
        csv_path = self._convert_name_to_path(table_name)
        if csv_path.exists():
            csv_path.unlink()
        else:
            raise FileNotFoundError(f"Table {table_name} wasn't found")

    def list_tables(self) -> list[Path]:
        tables = []
        for file in self._folder_path.iterdir():
            if file.suffix.lower() == ".csv":
                tables.append(file)
        return tables
