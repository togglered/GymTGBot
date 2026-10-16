from pathlib import Path
from typing import Any, cast

import pytest

from gym_tg_bot.tools.base import ToolContext
from gym_tg_bot.tools.workouts.add_workout import AddWorkoutTool
from gym_tg_bot.tools.workouts.query_workout import QueryWorkoutTool
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


NEW_EXERCISES = [
    ("biceps_curl", ExerciseLabel.BICEPS_CURL),
    ("dumbbell_shrug", ExerciseLabel.DUMBBELL_SHRUG),
    ("dumbbell_lateral_raise", ExerciseLabel.DUMBBELL_LATERAL_RAISE),
    ("hack_squat", ExerciseLabel.HACK_SQUAT),
    ("triceps_pushdown", ExerciseLabel.TRICEPS_PUSHDOWN),
    ("horizontal_row_wide_grip", ExerciseLabel.HORIZONTAL_ROW_WIDE_GRIP),
    ("horizontal_row_parallel_grip", ExerciseLabel.HORIZONTAL_ROW_PARALLEL_GRIP),
    ("vertical_pulldown_wide_grip", ExerciseLabel.VERTICAL_PULLDOWN_WIDE_GRIP),
    ("vertical_pulldown_parallel_grip", ExerciseLabel.VERTICAL_PULLDOWN_PARALLEL_GRIP),
    ("calf_raise", ExerciseLabel.CALF_RAISE),
    ("hamstring_curl", ExerciseLabel.HAMSTRING_CURL),
    ("incline_bench_press", ExerciseLabel.INCLINE_BENCH_PRESS),
    ("pull_up", ExerciseLabel.PULL_UP),
]


def test_exercise_values_are_stable() -> None:
    # the values are stored in the database, renaming one would orphan the old rows
    assert [e.value for e in ExerciseLabel] == [
        "bench_press",
        "squat",
        "deadlift",
        "biceps_curl",
        "dumbbell_shrug",
        "dumbbell_lateral_raise",
        "hack_squat",
        "triceps_pushdown",
        "horizontal_row_wide_grip",
        "horizontal_row_parallel_grip",
        "vertical_pulldown_wide_grip",
        "vertical_pulldown_parallel_grip",
        "calf_raise",
        "hamstring_curl",
        "incline_bench_press",
        "pull_up",
    ]


@pytest.mark.parametrize(("value", "label"), NEW_EXERCISES)
def test_new_exercises_are_offered_to_the_model(
    workout_store: WorkoutStore, value: str, label: ExerciseLabel
) -> None:
    add = cast(dict[str, Any], AddWorkoutTool(workout_store).definition)["function"]
    query = cast(dict[str, Any], QueryWorkoutTool(workout_store).definition)["function"]

    add_enum = add["parameters"]["properties"]["exercises"]["items"]["properties"]["label"]["enum"]
    query_enum = query["parameters"]["properties"]["label"]["enum"]
    assert value in add_enum
    assert value in query_enum
    assert label.value == value


@pytest.mark.asyncio
@pytest.mark.parametrize(("value", "label"), NEW_EXERCISES)
async def test_new_exercises_can_be_logged_and_queried(
    workout_store: WorkoutStore, value: str, label: ExerciseLabel
) -> None:
    context = ToolContext(chat_id=123)

    added = await AddWorkoutTool(workout_store)(
        {"exercises": [{"label": value, "sets": [{"reps": 12, "weight": 20.0}]}]}, context
    )
    queried = await QueryWorkoutTool(workout_store)({"label": value}, context)

    assert added == "Added 1 exercises"
    assert f", {value}, set #1: 20.0X12" in queried
    rows = await workout_store.query(123, label)
    assert [(r.exercise, r.reps, r.weight) for r in rows] == [(label, 12, 20.0)]


@pytest.mark.asyncio
async def test_exercises_do_not_leak_into_each_other(workout_store: WorkoutStore) -> None:
    await AddWorkoutTool(workout_store)(
        {"exercises": [{"label": "hack_squat", "sets": [{"reps": 10, "weight": 100.0}]}]},
        ToolContext(chat_id=123),
    )

    assert await workout_store.query(123, ExerciseLabel.SQUAT) == []
    assert len(await workout_store.query(123, ExerciseLabel.HACK_SQUAT)) == 1
