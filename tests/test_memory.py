from gym_tg_bot.memory import _MAX_HISTORY, ThreadMemory


def test_thread_memory() -> None:
    mem = ThreadMemory()
    mem.add(chat_id=1, thread_id=10, role="user", content="hello")
    mem.add(chat_id=1, thread_id=10, role="assistant", content="hi")

    assert mem.get(1, 10) == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ]


def test_memory_capacity() -> None:
    mem = ThreadMemory()
    for i in range(_MAX_HISTORY + 10):
        mem.add(chat_id=1, thread_id=10, role="user", content=f"msg-{i}")
    history = mem.get(chat_id=1, thread_id=10)
    assert len(history) == _MAX_HISTORY
    assert history[0]["content"] == "msg-10"
    assert history[-1]["content"] == f"msg-{_MAX_HISTORY + 9}"


def test_memory_isolation() -> None:
    mem = ThreadMemory()
    mem.add(1, 100, "user", "in thread A")
    mem.add(1, 200, "user", "in thread B")

    assert mem.get(1, 100) == [{"role": "user", "content": "in thread A"}]
    assert mem.get(1, 200) == [{"role": "user", "content": "in thread B"}]


def test_unknown_thread_returns_empty_list() -> None:
    assert ThreadMemory().get(1, 1) == []
