import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import StrEnum, auto
from pathlib import Path

import aiosqlite


class ExerciseLabel(StrEnum):
    BENCH_PRESS = auto()
    SQUAT = auto()
    DEADLIFT = auto()


@dataclass(frozen=True)
class SetEntry:
    reps: int
    weight: float


@dataclass(frozen=True)
class ExerciseEntry:
    label: ExerciseLabel
    sets: list[SetEntry]


@dataclass(frozen=True)
class WorkoutResult:
    performed_at: int
    exercise: ExerciseLabel
    set_number: int
    reps: int
    weight: float


class WorkoutStore:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    @asynccontextmanager
    async def _connect(self) -> AsyncIterator[aiosqlite.Connection]:
        db = await aiosqlite.connect(self._db_path)
        await db.execute("PRAGMA foreign_keys = ON")
        try:
            yield db
        finally:
            await db.close()

    async def ensure_schema(self) -> None:
        async with self._connect() as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS workouts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    performed_at INTEGER NOT NULL,
                    created_at INTEGER NOT NULL
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS workout_sets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workout_id INTEGER NOT NULL,
                    exercise TEXT NOT NULL,
                    set_number INTEGER NOT NULL,
                    reps INTEGER NOT NULL,
                    weight REAL NOT NULL,
                    FOREIGN KEY (workout_id) REFERENCES workouts(id) ON DELETE CASCADE
                )
                """
            )
            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS ix_workouts_chat ON workouts (chat_id, performed_at);
                """
            )
            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS ix_sets_workout ON workout_sets (workout_id);
                """
            )
            await db.commit()

    async def add_workout(self, chat_id: int, exercises: list[ExerciseEntry]) -> None:
        async with self._connect() as db:
            cursor = await db.execute(
                "INSERT INTO workouts (chat_id, performed_at, created_at) VALUES (?, ?, ?)",
                (chat_id, int(time.time()), int(time.time())),
            )
            workout_id: int | None = cursor.lastrowid
            assert workout_id is not None
            rows: list[tuple[int, str, int, int, float]] = []
            for exercise in exercises:
                for num, set_entry in enumerate(exercise.sets, 1):
                    rows.append(
                        (workout_id, exercise.label.value, num, set_entry.reps, set_entry.weight)
                    )
            await db.executemany(
                "INSERT INTO workout_sets (workout_id, exercise, set_number, reps, weight) "
                "VALUES (?, ?, ?, ?, ?)",
                rows,
            )
            await db.commit()

    async def query(
        self,
        chat_id: int,
        exercise: ExerciseLabel | None,
    ) -> list[WorkoutResult]:
        conditions = ["w.chat_id = ?"]
        params: list[str | int] = [chat_id]

        if exercise is not None:
            conditions.append("s.exercise = ?")
            params.append(exercise.value)

        where = " AND ".join(conditions)
        async with self._connect() as db:
            cursor = await db.execute(
                "SELECT w.performed_at, s.exercise, s.set_number, s.reps, s.weight "
                "FROM workout_sets s JOIN workouts w ON s.workout_id = w.id "
                f"WHERE {where}",
                params,
            )
            rows = await cursor.fetchall()
            return [
                WorkoutResult(
                    performed_at=row[0],
                    exercise=ExerciseLabel(row[1]),
                    set_number=row[2],
                    reps=row[3],
                    weight=row[4],
                )
                for row in rows
            ]
