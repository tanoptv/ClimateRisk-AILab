from typing import Any

from bot.messages import build_daily_flex_payload, build_daily_text_preview, build_emergency_text
from db.database import save_preview_notification


class NotificationRouter:
    def __init__(self, mode: str, db_path: str):
        self.mode = mode
        self.db_path = db_path

    def send_daily_summary(self, user_id: str, province: str, risks: list[dict[str, Any]]) -> None:
        payload = build_daily_flex_payload(province, risks)
        text_preview = build_daily_text_preview(province, risks)
        if self.mode == "dashboard":
            save_preview_notification(
                "daily_summary",
                user_id,
                province,
                None,
                text_preview,
                payload,
                db_path=self.db_path,
            )
            return

        from bot.line_bot import push_flex_message

        push_flex_message(user_id, f"รายงานความเสี่ยง {province}", payload)

    def send_emergency_alert(
        self,
        user_id: str,
        province: str,
        hazard_type: str,
        hazard_label: str,
        score: int,
        explanation: str,
    ) -> None:
        text = build_emergency_text(province, hazard_label, score, explanation)
        if self.mode == "dashboard":
            save_preview_notification(
                "emergency_alert",
                user_id,
                province,
                hazard_type,
                text,
                None,
                db_path=self.db_path,
            )
            return

        from bot.line_bot import push_text_message

        push_text_message(user_id, text)

