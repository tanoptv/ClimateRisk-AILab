import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


DB_PATH = "climate_risk.db"


def utcnow_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                provinces TEXT,
                created_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS risk_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                province TEXT,
                hazard_type TEXT,
                score INTEGER,
                raw_value REAL,
                explanation TEXT,
                checked_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts_sent (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                province TEXT,
                hazard_type TEXT,
                score INTEGER,
                sent_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS preview_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_type TEXT,
                user_id TEXT,
                province TEXT,
                hazard_type TEXT,
                text_preview TEXT,
                payload_json TEXT,
                created_at TEXT
            )
            """
        )


def save_user_provinces(user_id: str, provinces: list[str], db_path: str = DB_PATH) -> None:
    clean_provinces = [p.strip() for p in provinces if p.strip()]
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO users (user_id, provinces, created_at)
            VALUES (?, ?, ?)
            """,
            (user_id, ",".join(clean_provinces), utcnow_iso()),
        )


def get_user_provinces(user_id: str, db_path: str = DB_PATH) -> list[str]:
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT provinces FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    if not row or not row["provinces"]:
        return []
    return [p.strip() for p in row["provinces"].split(",") if p.strip()]


def get_all_users(db_path: str = DB_PATH) -> list[tuple[str, str]]:
    with get_connection(db_path) as conn:
        rows = conn.execute("SELECT user_id, provinces FROM users").fetchall()
    return [(row["user_id"], row["provinces"] or "") for row in rows]


def save_risk_log(
    province: str,
    hazard_type: str,
    score: int,
    raw_value: float,
    explanation: str,
    db_path: str = DB_PATH,
) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO risk_log (province, hazard_type, score, raw_value, explanation, checked_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (province, hazard_type, score, raw_value, explanation, utcnow_iso()),
        )


def get_latest_risk(province: str, db_path: str = DB_PATH) -> list[dict[str, Any]]:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT rl.hazard_type, rl.score, rl.raw_value, rl.explanation, rl.checked_at
            FROM risk_log rl
            JOIN (
                SELECT hazard_type, MAX(id) AS max_id
                FROM risk_log
                WHERE province = ?
                GROUP BY hazard_type
            ) latest ON latest.max_id = rl.id
            ORDER BY rl.hazard_type
            """,
            (province,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_recent_risk_logs(limit: int = 50, db_path: str = DB_PATH) -> list[dict[str, Any]]:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT province, hazard_type, score, raw_value, explanation, checked_at
            FROM risk_log
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def was_alert_sent_recently(
    user_id: str,
    province: str,
    hazard_type: str,
    hours: int = 6,
    db_path: str = DB_PATH,
) -> bool:
    cutoff = (datetime.now(UTC) - timedelta(hours=hours)).isoformat()
    with get_connection(db_path) as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM alerts_sent
            WHERE user_id = ? AND province = ? AND hazard_type = ? AND sent_at > ?
            """,
            (user_id, province, hazard_type, cutoff),
        ).fetchone()
    return bool(row and row["count"] > 0)


def save_alert_sent(
    user_id: str,
    province: str,
    hazard_type: str,
    score: int,
    db_path: str = DB_PATH,
) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO alerts_sent (user_id, province, hazard_type, score, sent_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, province, hazard_type, score, utcnow_iso()),
        )


def save_preview_notification(
    notification_type: str,
    user_id: str,
    province: str,
    hazard_type: str | None,
    text_preview: str,
    payload: dict[str, Any] | None = None,
    db_path: str = DB_PATH,
) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO preview_notifications
            (notification_type, user_id, province, hazard_type, text_preview, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                notification_type,
                user_id,
                province,
                hazard_type,
                text_preview,
                json.dumps(payload, ensure_ascii=False) if payload is not None else "",
                utcnow_iso(),
            ),
        )


def get_preview_notifications(limit: int = 25, db_path: str = DB_PATH) -> list[dict[str, Any]]:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT notification_type, user_id, province, hazard_type, text_preview, payload_json, created_at
            FROM preview_notifications
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def clear_preview_notifications(db_path: str = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.execute("DELETE FROM preview_notifications")


def load_provinces(path: str | Path = "data/provinces.json") -> dict[str, dict[str, float]]:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)
