# GymTGBot

A Telegram AI agent for tracking gym progress. It replies in isolated chat threads, remembers long-term facts, stores workout history, and analyzes photos.

## Features

* Keeps conversations isolated by chat and thread.
* Uses a tool-calling loop and can call multiple tools in a single response.
* Analyzes photos, including meals and physique updates.
* Stores long-term memory, such as injuries, preferences, and recurring issues.
* Tracks workout history, including weights, reps, and progression.
* Manages per-chat CSV tables, such as diet and training plans: create, list, read, update, and delete.

## Architecture

* `handlers/` and `middleware/` — Telegram integration powered by `aiogram`.
* `services/` — business logic and application services.
* `tools/` — LLM tool functions, such as `add_workout`, `query_workout`, `create_table`, and others.
* SQLite — workout tracking and isolated thread memory.
* CSV files — per-chat tables stored in `data/csvs/<chat_id>/` (configurable via `CSV_FOLDER_PATH`).

## Requirements

* Python 3.12+
* [uv](https://docs.astral.sh/uv/)
* Telegram Bot API token
* OpenAI API token

## Installation and Running

```bash
uv sync                      # Install dependencies
cp .env.example .env         # Fill in the required environment variables
uv run python -m gym_tg_bot  # Start the application
```

## Development

```bash
uv run pytest                              # Run tests
uv run ruff format . && uv run ruff check . # Format and lint
uv run mypy src tests                      # Run type checks
```
