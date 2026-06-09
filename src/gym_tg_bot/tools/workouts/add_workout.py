from typing import cast

from gym_tg_bot.tools.base import Tool, ToolContext
from gym_tg_bot.workouts import ExerciseDict, ExerciseEntry, ExerciseLabel, SetEntry, WorkoutStore


class AddWorkoutTool(Tool):
    def __init__(self, store: WorkoutStore) -> None:
        self._store = store

    @property
    def definition(self) -> dict[str, object]:
        return {
            "type": "function",
            "function": {
                "name": "add_workout",
                "description": "Add workout to database.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "exercises": {
                            "type": "array",
                            "description": "Exercises performed in the workout.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "label": {
                                        "type": "string",
                                        "enum": [e.value for e in ExerciseLabel],
                                    },
                                    "sets": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "reps": {"type": "integer"},
                                                "weight": {"type": "number"},
                                            },
                                            "required": ["reps", "weight"],
                                        },
                                    },
                                },
                                "required": ["label", "sets"],
                            },
                        },
                    },
                    "required": ["exercises"],
                },
            },
        }

    async def __call__(self, arguments: dict[str, object], context: ToolContext) -> str:
        exercises = cast(list[ExerciseDict], arguments["exercises"])
        exercises_list: list[ExerciseEntry] = []

        for exc in exercises:
            try:
                label = ExerciseLabel(exc["label"])
            except ValueError:
                return f"Exercise with {exc['label']} label wasn't found"
            exercises_list.append(
                ExerciseEntry(
                    label=label,
                    sets=[
                        SetEntry(reps=set_dict["reps"], weight=set_dict["weight"])
                        for set_dict in exc["sets"]
                    ],
                )
            )

        await self._store.add_workout(chat_id=context.chat_id, exercises=exercises_list)

        return f"Added {len(exercises_list)} exercises"
