# SPEC.md — Climate Risk Line Bot

## Summary

Climate Risk Line Bot is a Python MVP that lets LINE users subscribe to Thai provinces and receive natural-disaster risk information. The system checks risks hourly, stores results in SQLite, sends daily Flex Message summaries at 07:00 Asia/Bangkok, and sends immediate plain-text emergency alerts when a risk score reaches 5. During development, the app also provides a local dashboard so the team can test summaries and alerts without sending real LINE notifications.

## Functional Spec

### User Commands

Supported LINE text commands:

- `/ติดตาม <จังหวัด...>` subscribes the user to one or more provinces.
- `/จังหวัดของฉัน` lists the user's subscribed provinces.
- `/ช่วยเหลือ` shows available commands.

Command behavior:

- Province names must be matched against `data/provinces.json`.
- If no province is provided for `/ติดตาม`, reply with a usage example.
- If at least one provided province is invalid, reply with the invalid names and do not save partial invalid data.
- If all provinces are valid, save the full province list for the user and reply with confirmation.
- Unknown messages reply with a short help hint.

### Province Data

Province coordinates live in:

```text
data/provinces.json
```

Shape:

```json
{
  "เชียงใหม่": {"lat": 18.7883, "lon": 98.9853}
}
```

MVP target is all 77 Thai provinces. During early scaffolding, tests may use a smaller fixture, but production data should be complete before real demo.

### Hazards

The system tracks six hazards:

- `flood` — น้ำท่วม
- `pm25` — ฝุ่น PM2.5
- `drought` — ภัยแล้ง
- `storm` — พายุ
- `earthquake` — แผ่นดินไหว
- `fire` — ไฟป่า

External data mapping:

- Open-Meteo: flood, drought, storm
- OpenAQ: PM2.5
- USGS Earthquake API: earthquake
- NASA FIRMS: fire

### Risk Scoring

Scoring is deterministic code, not LLM judgment. Each scorer returns:

```python
tuple[int, float]  # score, raw_value
```

Thresholds:

| Hazard | Score 2 | Score 3 | Score 4 | Score 5 |
| --- | --- | --- | --- | --- |
| flood, precipitation max mm/hr | >= 10 | >= 20 | >= 35 | >= 50 |
| pm25, micrograms per m3 | >= 50 | >= 100 | >= 150 | >= 200 |
| drought, precipitation mm/day | < 5 | < 1 | == 0 | n/a |
| storm, wind km/h | >= 20 | >= 40 | >= 65 | >= 90 |
| earthquake, magnitude | >= 4.0 | >= 5.0 | >= 6.0 | >= 7.0 |
| fire, count or FRP | count >= 1 | count >= 5 or FRP >= 50 | count >= 10 or FRP >= 200 | count >= 20 or FRP >= 500 |

### LLM Explanation

Use Anthropic Claude Haiku model:

```text
claude-haiku-4-5-20251001
```

Behavior:

- If score <= 1, return `สถานการณ์ปกติ ไม่มีความเสี่ยงในขณะนี้` and do not call Anthropic.
- If score >= 2, send province, hazard type, score, and raw value to Claude.
- Output must be Thai, readable by general public, and about 2-3 sentences.
- The explanation should include reason, possible impact, and practical advice.

### Persistence

SQLite tables:

```sql
users(user_id TEXT PRIMARY KEY, provinces TEXT, created_at TEXT)
risk_log(id INTEGER PRIMARY KEY AUTOINCREMENT, province TEXT, hazard_type TEXT, score INTEGER, raw_value REAL, explanation TEXT, checked_at TEXT)
alerts_sent(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, province TEXT, hazard_type TEXT, score INTEGER, sent_at TEXT)
```

### Scheduler Behavior

Hourly check:

- Load all users and subscribed provinces.
- Deduplicate province fetches across users.
- Fetch current external data for each watched province.
- Score all six hazards.
- Generate explanations.
- Save all risk rows.
- For score 5 risks, send emergency alerts to subscribed users unless already sent in the last 6 hours.

Daily summary:

- Runs at 07:00 Asia/Bangkok.
- For each user and subscribed province, load latest risk rows from SQLite.
- Send one Flex Message per province.
- Do not call external APIs during summary sending.

### Dashboard Test Mode

The app must include a local dashboard for development and demo testing before real LINE notification is enabled.

Dashboard route:

- `GET /dashboard` shows latest risk data, watched users/provinces, and generated notification previews.
- `POST /dashboard/run-hourly-check` triggers the same hourly risk workflow used by the scheduler.
- `POST /dashboard/send-daily-summary` triggers daily summary generation for subscribed users.
- `POST /dashboard/clear-preview-notifications` clears dashboard-only preview notifications.

Notification mode:

- `NOTIFICATION_MODE=line` sends real LINE push/reply messages.
- `NOTIFICATION_MODE=dashboard` does not push to LINE. It stores generated daily summaries and emergency alerts as preview notifications for `/dashboard`.
- Default local development mode is `dashboard`.
- LINE webhook command replies may still be implemented and tested separately, but scheduled push notifications must be blocked in dashboard mode.

Dashboard preview notifications must include:

- notification type: `daily_summary` or `emergency_alert`
- target user id
- province
- hazard type when applicable
- text preview or Flex payload JSON
- created timestamp

### Message Formats

Emergency alert:

- Plain LINE text message.
- Must include province, hazard label, score 5/5, and practical advice.

Daily summary:

- LINE Flex Message.
- Must include province name.
- Must show all six hazards when available.
- Each hazard row shows label, score, color/progress indicator, and explanation.

## Non-Functional Spec

- The app runs locally on port `8000` by default.
- LINE webhook is exposed during development via ngrok.
- Fetcher failures are isolated; one failed source must not stop other hazards.
- Automated tests must not call live external services.
- Secrets live in `.env`; `.env` is never committed.
- Dashboard mode must be available without valid LINE channel credentials.

## Acceptance Criteria

- A user can subscribe to valid provinces and see them via `/จังหวัดของฉัน`.
- Invalid provinces are rejected with a useful Thai reply.
- Hourly check can process watched provinces and write six risk rows per province.
- Score 5 produces an emergency text alert once per dedupe window.
- Daily summary sends a Flex Message from stored risk rows.
- Dashboard mode can generate and preview daily summaries and emergency alerts without calling the LINE push API.
- Score 1 explanation path does not call Anthropic.
- Test suite covers scorer boundaries and key no-live-API behavior.
