# AGENTS.md — Climate Risk Line Bot

This file is the working contract for AI agents and engineers implementing this repo.

## Project Intent

Build a Python LINE Bot that monitors climate and natural-disaster risk for Thai provinces, stores hourly risk checks in SQLite, sends daily summaries at 07:00 Asia/Bangkok, and pushes emergency alerts when any hazard reaches score 5.

Primary source documents:

- `PRD.md` — product requirements and implementation decisions
- `build-guide.md` — baseline implementation guide and example code
- `SPEC.md` — implementation-ready behavioral spec
- `TASKS.md` — build checklist

## Implementation Style

Use a hardened MVP approach:

- Keep the PRD scope, but structure code so it is testable and easy to extend.
- Prefer small pure functions for parsing, scoring, formatting, and command handling.
- Keep external SDK/API calls behind thin wrapper functions or injectable clients.
- Validate user input, especially province names, before saving it.
- Avoid hidden global side effects where practical. Environment loading should happen at application startup.

## Architecture Rules

Use these module boundaries:

- `fetchers/` fetches and normalizes external API data only.
- `scorer/` contains pure scoring functions only.
- `llm/` creates Thai explanations from already computed scores.
- `bot/` handles Flask routes, LINE message parsing, replies, pushes, and Flex payload construction.
- `dashboard/` or dashboard-specific `bot/` routes expose local testing screens and actions.
- `db/` owns SQLite schema and CRUD functions.
- `main.py` orchestrates startup, scheduler jobs, hourly checks, and daily summaries.

Do not put business logic directly in `main.py` or inside Flask route handlers if it can be tested as a separate function.

## Data And Time Rules

- Store user province subscriptions as comma-separated text in `users.provinces` for MVP compatibility with the PRD.
- Store timestamps as ISO 8601 text.
- Scheduler timezone is `Asia/Bangkok`.
- Daily summaries use latest rows from `risk_log`; they do not refetch APIs.
- Emergency alert dedupe window is 6 hours per user, province, and hazard type.
- `NOTIFICATION_MODE=dashboard` must never call LINE push APIs; generated notifications are previewed locally instead.

## Coding Rules

- Python 3.10+.
- Use `requests` for HTTP in the MVP unless the project later chooses async.
- Use `python-dotenv` for local environment loading.
- Use `pytest` for tests.
- Use clear type hints for public functions.
- External fetcher failures must return zero-value defaults and must not crash the hourly check.
- Score 1 must not call the Anthropic API; return the default Thai normal-status message.

## Testing Expectations

Prioritize tests for:

- Scorer threshold boundaries.
- Fetcher success and failure normalization with mocked HTTP responses.
- LLM score 1 no-call behavior and score >= 2 prompt/client behavior.
- DB CRUD using an isolated temporary SQLite database or in-memory connection.
- Bot command parsing and province validation without calling LINE APIs.
- Dashboard notification routing, especially that dashboard mode does not call LINE push APIs.

Do not rely on live external APIs in automated tests.

## Secrets

- Never commit `.env`, database files, API keys, or channel tokens.
- Keep `.env.example` updated when environment variables change.

## Commands

Expected local commands once implementation exists:

```bash
python -m venv .venv
pip install -r requirements.txt
pytest
python main.py
```
