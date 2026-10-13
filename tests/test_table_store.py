from pathlib import Path
from typing import cast

import pytest

from gym_tg_bot.table_store import TableStore


@pytest.fixture
def store(tmp_path: Path) -> TableStore:
    return TableStore(tmp_path)


@pytest.mark.parametrize("bad_name", ["", "../etc", "a/b", "a b", "with.dot", "x" * 65, "юникод"])
def test_invalid_name_raises(store: TableStore, bad_name: str) -> None:
    with pytest.raises(ValueError):
        store.create_table(
            123, bad_name, [["meal", "protein", "fat", "carbs"], ["chicken", "20", "4", "0"]]
        )


@pytest.mark.parametrize("ok_name", ["a", "A-b_1", "x" * 64])
def test_valid_name_ok(store: TableStore, ok_name: str) -> None:
    store.create_table(
        123, ok_name, [["meal", "protein", "fat", "carbs"], ["chicken", "20", "4", "0"]]
    )


def test_create_table(store: TableStore) -> None:
    csv_path = store.create_table(
        123, "123", content=[["meal", "protein", "fat", "carbs"], ["chicken", "20", "4", "0"]]
    )
    tables = store.list_tables(123)
    assert csv_path in tables


def test_create_existing_table(store: TableStore) -> None:
    store.create_table(
        123, "123", content=[["meal", "protein", "fat", "carbs"], ["chicken", "20", "4", "0"]]
    )
    with pytest.raises(FileExistsError):
        store.create_table(
            123,
            "123",
            content=[
                ["meal", "protein", "fat", "carbs"],
                ["chicken", "20", "4", "0"],
            ],
        )


def test_create_empty_content(store: TableStore) -> None:
    store.create_table(123, "empty", [])
    assert store.read_table(123, "empty") == ""


def test_update_table(store: TableStore) -> None:
    store.create_table(
        123, "123", content=[["meal", "protein", "fat", "carbs"], ["chicken", "20", "4", "0"]]
    )
    store.update_table(
        123, "123", content=[["meal", "protein", "fat", "carbs"], ["rice", "3", "1", "25"]]
    )
    content = store.read_table(123, "123")
    assert content == "meal,protein,fat,carbs\nrice,3,1,25\n"


def test_read_not_existing_table(store: TableStore) -> None:
    with pytest.raises(FileNotFoundError):
        store.read_table(123, "some_table")


def test_update_non_exisitng_table(store: TableStore) -> None:
    with pytest.raises(FileNotFoundError):
        store.update_table(
            123, "123", [["meal", "protein", "fat", "carbs"], ["rice", "3", "1", "25"]]
        )


def test_delete_table(store: TableStore) -> None:
    table = store.create_table(
        123, "123", [["meal", "protein", "fat", "carbs"], ["rice", "3", "1", "25"]]
    )
    store.delete_table(123, "123")
    tables = store.list_tables(123)
    assert table not in tables
    with pytest.raises(FileNotFoundError):
        store.read_table(123, "123")


def test_delete_non_existing_table(store: TableStore) -> None:
    with pytest.raises(FileNotFoundError):
        store.delete_table(123, "some_table")


def test_create_escapes_special_chars(store: TableStore) -> None:
    store.create_table(123, "t", [["a,b", 'quote"here']])
    assert store.read_table(123, "t") == '"a,b","quote""here"\n'


def test_list_tables_empty(store: TableStore) -> None:
    assert store.list_tables(123) == []


def test_list_tables_many(store: TableStore) -> None:
    table1 = store.create_table(
        123, "1", [["meal", "protein", "fat", "carbs"], ["chicken", "20", "4", "0"]]
    )
    table2 = store.create_table(
        123, "2", [["meal", "protein", "fat", "carbs"], ["rice", "3", "1", "25"]]
    )

    assert set(store.list_tables(123)) == {table2, table1}


def test_list_tables_non_csv(store: TableStore) -> None:
    csv_path = store.create_table(123, "real", [["a"]])
    (store._folder_path / "123" / "file.txt").touch()
    assert store.list_tables(123) == [csv_path]


def test_list_tables_isolated(store: TableStore) -> None:
    store.create_table(1, "a", [["x"]])
    store.create_table(2, "b", [["y"]])
    assert [p.name for p in store.list_tables(1)] == ["a.csv"]


def test_isolation_between_chats(store: TableStore) -> None:
    store.create_table(1, "diet", [["chicken"]])
    store.create_table(2, "diet", [["rice"]])

    assert store.read_table(1, "diet") == "chicken\n"
    assert store.read_table(2, "diet") == "rice\n"


@pytest.mark.parametrize(
    "bad_content",
    [
        ["meal", "protein"],
        [1, 2],
        "abc",
        None,
        {"meal": "protein"},
        [["meal"], "chicken"],
        [["meal", ["nested"]]],
        [["meal", {"a": 1}]],
    ],
)
def test_create_invalid_content_raises(store: TableStore, bad_content: object) -> None:
    with pytest.raises(ValueError, match="Invalid table content"):
        store.create_table(123, "diet", cast(list[list[object]], bad_content))
    assert store.list_tables(123) == []


@pytest.mark.parametrize("bad_content", [["meal", "protein"], [1, 2], [["meal"], "chicken"]])
def test_update_invalid_content_keeps_table(store: TableStore, bad_content: object) -> None:
    store.create_table(123, "diet", [["meal"], ["chicken"]])
    with pytest.raises(ValueError, match="Invalid table content"):
        store.update_table(123, "diet", cast(list[list[object]], bad_content))
    assert store.read_table(123, "diet") == "meal\nchicken\n"


def test_scalar_cells_are_accepted(store: TableStore) -> None:
    store.create_table(123, "mixed", [["meal", "protein"], ["chicken", 20], ["rice", 7.5, None]])
    assert store.read_table(123, "mixed") == "meal,protein\nchicken,20\nrice,7.5,\n"
