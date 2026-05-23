import importlib


def test_import_package() -> None:
    module = importlib.import_module("gym_tg_bot")

    assert module is not None
