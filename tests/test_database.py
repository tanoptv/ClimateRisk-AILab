from db import database
from tests.helpers import temp_db_path


def test_user_provinces_round_trip():
    db_path = temp_db_path()
    database.init_db(db_path)
    database.save_user_provinces("u1", ["เชียงใหม่", "กรุงเทพมหานคร"], db_path)
    assert database.get_user_provinces("u1", db_path) == ["เชียงใหม่", "กรุงเทพมหานคร"]
    assert database.get_all_users(db_path) == [("u1", "เชียงใหม่,กรุงเทพมหานคร")]


def test_latest_risk_returns_latest_per_hazard():
    db_path = temp_db_path()
    database.init_db(db_path)
    database.save_risk_log("เชียงใหม่", "flood", 2, 10, "old", db_path)
    database.save_risk_log("เชียงใหม่", "flood", 5, 55, "new", db_path)
    database.save_risk_log("เชียงใหม่", "pm25", 3, 100, "dust", db_path)
    rows = database.get_latest_risk("เชียงใหม่", db_path)
    by_hazard = {row["hazard_type"]: row for row in rows}
    assert by_hazard["flood"]["score"] == 5
    assert by_hazard["pm25"]["explanation"] == "dust"


def test_alert_dedupe_and_preview_notifications():
    db_path = temp_db_path()
    database.init_db(db_path)
    assert not database.was_alert_sent_recently("u1", "เชียงใหม่", "flood", db_path=db_path)
    database.save_alert_sent("u1", "เชียงใหม่", "flood", 5, db_path)
    assert database.was_alert_sent_recently("u1", "เชียงใหม่", "flood", db_path=db_path)

    database.save_preview_notification("emergency_alert", "u1", "เชียงใหม่", "flood", "alert", None, db_path)
    previews = database.get_preview_notifications(db_path=db_path)
    assert previews[0]["notification_type"] == "emergency_alert"
    database.clear_preview_notifications(db_path)
    assert database.get_preview_notifications(db_path=db_path) == []
