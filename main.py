from __future__ import annotations

from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask

from app_config import Settings, load_settings
from bot.line_bot import line_blueprint, register_line_handlers
from bot.notifier import NotificationRouter
from dashboard.routes import dashboard_blueprint
from db import database
from fetchers.air_quality import fetch_pm25
from fetchers.earthquake import fetch_earthquake
from fetchers.fire import fetch_fire
from fetchers.weather import fetch_weather
from llm.analyzer import analyze_risk
from scorer.risk_scorer import HAZARD_LABELS, score_all


def check_risks_for_province(
    province: str,
    coords: dict[str, float],
    settings: Settings,
    db_path: str,
) -> list[dict[str, Any]]:
    lat, lon = coords["lat"], coords["lon"]
    weather = fetch_weather(lat, lon)
    pm25 = fetch_pm25(lat, lon)
    earthquake = fetch_earthquake(lat, lon)
    fire = fetch_fire(lat, lon, settings.nasa_firms_api_key)
    scores = score_all(weather, pm25, earthquake, fire)

    results = []
    for hazard, (score, raw_value) in scores.items():
        if score == 0:
            continue
        explanation = analyze_risk(province, hazard, score, raw_value)
        database.save_risk_log(province, hazard, score, raw_value, explanation, db_path=db_path)
        results.append(
            {
                "hazard": hazard,
                "hazard_type": hazard,
                "label": HAZARD_LABELS[hazard],
                "score": score,
                "raw_value": raw_value,
                "explanation": explanation,
            }
        )
    return results


def hourly_check(settings: Settings, provinces: dict[str, dict[str, float]], db_path: str) -> None:
    users = database.get_all_users(db_path=db_path)
    notifier = NotificationRouter(settings.notification_mode, db_path)
    user_provinces: dict[str, list[str]] = {}
    watched = set()

    for user_id, province_text in users:
        subscribed = [p.strip() for p in province_text.split(",") if p.strip()]
        user_provinces[user_id] = subscribed
        watched.update(p for p in subscribed if p in provinces)

    risk_cache = {
        province: check_risks_for_province(province, provinces[province], settings, db_path)
        for province in sorted(watched)
    }

    for user_id, subscribed in user_provinces.items():
        for province in subscribed:
            for risk in risk_cache.get(province, []):
                if risk["score"] == 5 and not database.was_alert_sent_recently(
                    user_id,
                    province,
                    risk["hazard"],
                    db_path=db_path,
                ):
                    notifier.send_emergency_alert(
                        user_id,
                        province,
                        risk["hazard"],
                        risk["label"],
                        risk["score"],
                        risk["explanation"],
                    )
                    database.save_alert_sent(user_id, province, risk["hazard"], risk["score"], db_path=db_path)


def daily_summary(settings: Settings, db_path: str) -> None:
    notifier = NotificationRouter(settings.notification_mode, db_path)
    for user_id, province_text in database.get_all_users(db_path=db_path):
        for province in [p.strip() for p in province_text.split(",") if p.strip()]:
            risks = database.get_latest_risk(province, db_path=db_path)
            if risks:
                notifier.send_daily_summary(user_id, province, risks)


def create_app(settings: Settings | None = None) -> Flask:
    settings = settings or load_settings()
    db_path = settings.db_path
    database.init_db(db_path)
    provinces = database.load_provinces()

    app = Flask(__name__)
    app.config["DB_PATH"] = db_path
    app.config["NOTIFICATION_MODE"] = settings.notification_mode
    app.config["HOURLY_CHECK"] = lambda: hourly_check(settings, provinces, db_path)
    app.config["DAILY_SUMMARY"] = lambda: daily_summary(settings, db_path)
    app.register_blueprint(dashboard_blueprint)
    app.register_blueprint(line_blueprint)
    register_line_handlers()
    return app


def start_scheduler(settings: Settings, provinces: dict[str, dict[str, float]], db_path: str) -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="Asia/Bangkok")
    scheduler.add_job(lambda: hourly_check(settings, provinces, db_path), "interval", hours=1, id="hourly_check")
    scheduler.add_job(lambda: daily_summary(settings, db_path), CronTrigger(hour=7, minute=0), id="daily_summary")
    scheduler.start()
    return scheduler


if __name__ == "__main__":
    app_settings = load_settings()
    app = create_app(app_settings)
    app_provinces = database.load_provinces()
    start_scheduler(app_settings, app_provinces, app_settings.db_path)
    print(f"Climate Risk Bot running on port {app_settings.port}")
    print(f"Notification mode: {app_settings.notification_mode}")
    print(f"Dashboard: http://localhost:{app_settings.port}/dashboard")
    app.run(host="0.0.0.0", port=app_settings.port)

