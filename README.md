# Climate Risk Line Bot

Python MVP for a Thai climate-risk LINE Bot with a local dashboard test mode.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Fill `.env` when using real external services. Local dashboard mode works without LINE credentials:

```env
NOTIFICATION_MODE=dashboard
```

## Run

```bash
python main.py
```

Open:

```text
http://localhost:8000/dashboard
```

Dashboard mode previews daily summaries and emergency alerts without pushing real LINE messages.

## Test

```bash
pytest
```

## LINE Webhook

For real LINE testing:

1. Set `NOTIFICATION_MODE=line`.
2. Add real `LINE_CHANNEL_SECRET` and `LINE_CHANNEL_ACCESS_TOKEN`.
3. Run `python main.py`.
4. Run `ngrok http 8000`.
5. Configure LINE webhook as `<ngrok-url>/callback`.

