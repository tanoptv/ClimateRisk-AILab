from bot.notifier import NotificationRouter
from db import database
from tests.helpers import temp_db_path


def test_dashboard_mode_stores_daily_preview():
    db_path = temp_db_path()
    database.init_db(db_path)
    router = NotificationRouter("dashboard", db_path)
    router.send_daily_summary(
        "u1",
        "เชียงใหม่",
        [{"hazard_type": "flood", "score": 5, "raw_value": 55, "explanation": "ฝนหนัก"}],
    )
    previews = database.get_preview_notifications(db_path=db_path)
    assert previews[0]["notification_type"] == "daily_summary"
    assert "เชียงใหม่" in previews[0]["text_preview"]
    assert previews[0]["payload_json"]


def test_dashboard_mode_stores_emergency_preview():
    db_path = temp_db_path()
    database.init_db(db_path)
    router = NotificationRouter("dashboard", db_path)
    router.send_emergency_alert("u1", "เชียงใหม่", "flood", "น้ำท่วม", 5, "หลีกเลี่ยงพื้นที่ลุ่ม")
    previews = database.get_preview_notifications(db_path=db_path)
    assert previews[0]["notification_type"] == "emergency_alert"
    assert "แจ้งเตือนฉุกเฉิน" in previews[0]["text_preview"]
