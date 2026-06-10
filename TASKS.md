# TASKS.md — Climate Risk Line Bot Implementation

## Phase 0 — Project Setup

- [ ] Create Python project structure from `AGENTS.md`.
- [ ] Add `requirements.txt` with runtime and test dependencies.
- [ ] Add `.gitignore` for `.env`, SQLite files, caches, and virtualenvs.
- [ ] Add `.env.example` and document required variables.
- [ ] Add minimal `README.md` with setup, run, test, and ngrok instructions.

## Phase 1 — Core Data And Scoring

- [ ] Add `data/provinces.json` with all 77 Thai provinces.
- [ ] Implement `db/database.py` schema initialization and CRUD functions.
- [ ] Implement `scorer/risk_scorer.py` thresholds and hazard labels.
- [ ] Add pytest coverage for scorer threshold boundaries.
- [ ] Add isolated DB tests for users, risk logs, latest risk lookup, and alert dedupe.

## Phase 2 — External Boundaries

- [ ] Implement Open-Meteo weather fetcher.
- [ ] Implement OpenAQ PM2.5 fetcher.
- [ ] Implement USGS earthquake fetcher.
- [ ] Implement NASA FIRMS fire fetcher.
- [ ] Add mocked fetcher tests for success, HTTP error, timeout, empty/null response.
- [ ] Implement `llm/analyzer.py` with score 1 no-call behavior.
- [ ] Add mocked LLM tests for no-call and prompt/client behavior.

## Phase 3 — LINE Bot

- [ ] Implement command parsing as testable pure functions.
- [ ] Implement province validation using loaded province data.
- [ ] Implement Flask `/callback` route and LINE webhook handler.
- [ ] Implement reply behavior for `/ติดตาม`, `/จังหวัดของฉัน`, `/ช่วยเหลือ`, and unknown text.
- [ ] Implement emergency alert text message builder.
- [ ] Implement daily summary Flex Message builder.
- [ ] Add tests for command parsing, province validation, and message payload builders.

## Phase 4 — Dashboard Test Mode

- [ ] Add `NOTIFICATION_MODE` config with `dashboard` as the local development default.
- [ ] Implement dashboard-only preview notification storage.
- [ ] Implement `GET /dashboard` showing users, watched provinces, latest risks, and notification previews.
- [ ] Implement dashboard actions to run hourly check, send daily summary, and clear preview notifications.
- [ ] Ensure dashboard mode never calls LINE push APIs for scheduled daily summaries or emergency alerts.
- [ ] Add tests for notification routing in `dashboard` vs `line` mode.

## Phase 5 — Orchestration

- [ ] Implement app configuration and environment loading.
- [ ] Implement `check_risks_for_province()`.
- [ ] Implement `hourly_check()` with province dedupe and emergency alert dedupe.
- [ ] Implement `daily_summary()` from latest DB rows.
- [ ] Wire APScheduler with hourly interval and 07:00 Asia/Bangkok cron.
- [ ] Wire Flask app startup on `PORT` defaulting to `8000`.

## Phase 6 — Demo Readiness

- [ ] Run full test suite locally.
- [ ] Run fetcher smoke test with real coordinates.
- [ ] Run local app with `.env`.
- [ ] Open `http://localhost:8000/dashboard`.
- [ ] Verify dashboard mode can preview notifications without LINE credentials.
- [ ] Start `ngrok http 8000`.
- [ ] Configure LINE webhook URL as `<ngrok-url>/callback`.
- [ ] Test LINE commands manually.
- [ ] Trigger a controlled score 5 scenario via test data or mocked check path.
- [ ] Confirm no duplicate emergency alert within 6 hours.

## Recommended First Implementation Order

1. Scaffold files and dependencies.
2. Implement scorer plus tests.
3. Implement DB plus tests.
4. Implement command parsing and province validation.
5. Implement fetchers and LLM wrapper.
6. Implement LINE messaging and Flex payloads.
7. Implement dashboard notification mode.
8. Implement scheduler orchestration.
9. Smoke test in dashboard mode before ngrok and real LINE channel.
