from pathlib import Path

import pytest

from gym_tg_bot.tools.base import ToolContext
from gym_tg_bot.tools.workouts.add_workout import AddWorkoutTool
from gym_tg_bot.workouts import ExerciseLabel, WorkoutStore


@pytest.fixture
async def workout_store(tmp_path: Path) -> WorkoutStore:
    store = WorkoutStore(tmp_path / "test.db")
    await store.ensure_schema()
    return store


@pytest.mark.asyncio
async def test_add_workout(workout_store: WorkoutStore) -> None:
    tool = AddWorkoutTool(workout_store)
    result = await tool(
        {"exercises": [{"label": "bench_press", "sets": [{"reps": 5, "weight": 100.0}]}]},
        ToolContext(chat_id=123),
    )
    assert result == "Added 1 exercises"
    rows = await workout_store.query(123, ExerciseLabel.BENCH_PRESS)
    assert rows[0].exercise == ExerciseLabel.BENCH_PRESS
    assert rows[0].reps == 5
    assert rows[0].weight == 100


@pytest.mark.asyncio
async def test_wrong_label(workout_store: WorkoutStore) -> None:
    tool = AddWorkoutTool(workout_store)
    result = await tool(
        {"exercises": [{"label": "something", "sets": [{"reps": 5, "weight": 100.0}]}]},
        ToolContext(chat_id=123),
    )
    assert "wasn't found" in result
    rows = await workout_store.query(123, ExerciseLabel.BENCH_PRESS)
    assert len(rows) == 0
