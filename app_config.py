import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str
    line_channel_secret: str
    line_channel_access_token: str
    nasa_firms_api_key: str
    port: int
    database_url: str
    notification_mode: str

    @property
    def db_path(self) -> str:
        if self.database_url.startswith("sqlite:///"):
            return self.database_url.removeprefix("sqlite:///")
        return self.database_url

    @property
    def is_dashboard_mode(self) -> bool:
        return self.notification_mode == "dashboard"


def load_settings() -> Settings:
    load_dotenv()
    mode = os.getenv("NOTIFICATION_MODE", "dashboard").strip().lower()
    if mode not in {"dashboard", "line"}:
        mode = "dashboard"

    database_url = os.getenv("DATABASE_URL", "sqlite:///climate_risk.db")
    if os.getenv("VERCEL") and database_url == "sqlite:///climate_risk.db":
        database_url = "sqlite:////tmp/climate_risk.db"

    return Settings(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        line_channel_secret=os.getenv("LINE_CHANNEL_SECRET", ""),
        line_channel_access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN", ""),
        nasa_firms_api_key=os.getenv("NASA_FIRMS_API_KEY", ""),
        port=int(os.getenv("PORT", "8000")),
        database_url=database_url,
        notification_mode=mode,
    )

