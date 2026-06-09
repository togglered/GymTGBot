from datetime import UTC, datetime

from gym_tg_bot.tools.base import Tool, ToolContext
from gym_tg_bot.workouts import ExerciseLabel, WorkoutStore


class QueryWorkoutTool(Tool):
    def __init__(self, store: WorkoutStore) -> None:
        self._store = store

    @property
    def definition(self) -> dict[str, object]:
        return {
            "type": "function",
            "function": {
                "name": "query_workout",
                "description": "Query workout from database.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "label": {
                            "type": "string",
                            "description": "Exercise's label to query.",
                            "enum": [e.value for e in ExerciseLabel],
                        },
                    },
                    "required": ["label"],
                },
            },
        }

    async def __call__(self, arguments: dict[str, object], context: ToolContext) -> str:
        exercise = ExerciseLabel(str(arguments["label"]))
        result = await self._store.query(
            chat_id=context.chat_id,
            exercise=exercise,
        )
        if not result:
            return "No workouts found."
        lines = []
        for workout in result:
            date = datetime.fromtimestamp(workout.performed_at, tz=UTC).strftime("%Y-%m-%d")
            lines.append(
                f"{date}, {workout.exercise},"
                f" set #{workout.set_number}: {workout.weight}X{workout.reps}"
            )
        return " | ".join(lines)
