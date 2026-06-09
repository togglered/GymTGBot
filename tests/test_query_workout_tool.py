from pathlib import Path

import pytest

from gym_tg_bot.tools.base import ToolContext
from gym_tg_bot.tools.workouts.query_workout import QueryWorkoutTool
from gym_tg_bot.workouts import ExerciseEntry, ExerciseLabel, SetEntry, WorkoutStore


@pytest.fixture
async def workout_store(tmp_path: Path) -> WorkoutStore:
    store = WorkoutStore(tmp_path / "test.db")
    await store.ensure_schema()
    return store


@pytest.mark.asyncio
async def test_query_output(workout_store: WorkoutStore) -> None:
    exc_entry = ExerciseEntry(
        label=ExerciseLabel.BENCH_PRESS,
        sets=[
            SetEntry(
                reps=2,
                weight=100.0,
            ),
            SetEntry(
                reps=4,
                weight=90.0,
            ),
        ],
    )
    await workout_store.add_workout(chat_id=123, exercises=[exc_entry])
    tool = QueryWorkoutTool(workout_store)
    result = await tool({"label": "bench_press"}, ToolContext(chat_id=123))
    assert "bench_press" in result
    assert "set #1" in result


@pytest.mark.asyncio
async def test_empty_query(workout_store: WorkoutStore) -> None:
    tool = QueryWorkoutTool(workout_store)
    result = await tool({"label": "bench_press"}, ToolContext(chat_id=123))
    assert result == "No workouts found."
