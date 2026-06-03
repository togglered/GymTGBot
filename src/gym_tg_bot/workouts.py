from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from enum import StrEnum, auto
from pathlib import Path

import aiosqlite


class ExerciseLabel(StrEnum):
    BENCH_PRESS = auto()
    SQUAT = auto()
    DEADLIFT = auto()


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
