from pathlib import Path

import pytest

from gym_tg_bot.workouts import ExerciseEntry, ExerciseLabel, SetEntry, WorkoutStore


@pytest.fixture
async def workout_store(tmp_path: Path) -> WorkoutStore:
    store = WorkoutStore(tmp_path / "test.db")
    await store.ensure_schema()
    return store


@pytest.mark.asyncio
async def test_ensure_schema_idempotent(workout_store: WorkoutStore) -> None:
    await workout_store.ensure_schema()


@pytest.mark.asyncio
async def test_add_and_query_round_trip(workout_store: WorkoutStore) -> None:
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

    result = await workout_store.query(
        chat_id=123,
        exercise=ExerciseLabel.BENCH_PRESS,
    )
    assert len(result) == 2

    assert result[0].exercise == ExerciseLabel.BENCH_PRESS
    assert result[0].set_number == 1
    assert result[0].reps == 2
    assert result[0].weight == 100.0

    assert result[1].set_number == 2
    assert result[1].reps == 4
    assert result[1].weight == 90.0

    assert result[0].performed_at > 0


@pytest.mark.asyncio
async def test_chat_isolation(workout_store: WorkoutStore) -> None:
    await workout_store.add_workout(
        chat_id=123,
        exercises=[
            ExerciseEntry(
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
        ],
    )
    await workout_store.add_workout(
        chat_id=900,
        exercises=[
            ExerciseEntry(
                label=ExerciseLabel.BENCH_PRESS,
                sets=[
                    SetEntry(
                        reps=5,
                        weight=106.0,
                    ),
                    SetEntry(
                        reps=1,
                        weight=110.0,
                    ),
                    SetEntry(
                        reps=10,
                        weight=80.0,
                    ),
                ],
            )
        ],
    )

    result = await workout_store.query(
        chat_id=123,
        exercise=ExerciseLabel.BENCH_PRESS,
    )
    assert len(result) == 2

    result = await workout_store.query(
        chat_id=900,
        exercise=ExerciseLabel.BENCH_PRESS,
    )

    assert len(result) == 3


@pytest.mark.asyncio
async def test_query_filters_by_exercise(workout_store: WorkoutStore) -> None:
    await workout_store.add_workout(
        chat_id=900,
        exercises=[
            ExerciseEntry(
                label=ExerciseLabel.BENCH_PRESS,
                sets=[
                    SetEntry(
                        reps=5,
                        weight=106.0,
                    ),
                ],
            ),
            ExerciseEntry(
                label=ExerciseLabel.SQUAT,
                sets=[
                    SetEntry(
                        reps=15,
                        weight=120.0,
                    ),
                ],
            ),
        ],
    )

    result = await workout_store.query(
        chat_id=900,
        exercise=ExerciseLabel.BENCH_PRESS,
    )

    assert all(r.exercise == ExerciseLabel.BENCH_PRESS for r in result)

    result = await workout_store.query(
        chat_id=900,
        exercise=ExerciseLabel.SQUAT,
    )

    assert all(r.exercise == ExerciseLabel.SQUAT for r in result)


@pytest.mark.asyncio
async def test_query_empty(workout_store: WorkoutStore) -> None:
    result = await workout_store.query(
        chat_id=123,
        exercise=ExerciseLabel.BENCH_PRESS,
    )

    assert len(result) == 0
