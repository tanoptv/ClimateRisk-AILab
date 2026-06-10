import html
import json

from flask import Blueprint, current_app, redirect, url_for
from flask import request

from scorer.risk_scorer import SCORE_COLORS, SCORE_LABELS
from db.database import (
    clear_preview_notifications,
    get_all_users,
    get_preview_notifications,
    get_recent_risk_logs,
    load_provinces,
    save_user_provinces,
)


dashboard_blueprint = Blueprint("dashboard", __name__)


@dashboard_blueprint.get("/")
def index():
    return redirect(url_for("dashboard.dashboard_home"))


def _page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="th">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; color: #111827; background: #f3f4f6; }}
    header {{ background: #111827; color: white; padding: 20px 28px; }}
    main {{ padding: 24px 28px; display: grid; gap: 18px; }}
    section {{ background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 18px; }}
    h1, h2 {{ margin: 0 0 10px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 8px; border-bottom: 1px solid #e5e7eb; text-align: left; vertical-align: top; }}
    code, pre {{ background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; }}
    pre {{ padding: 10px; overflow: auto; max-height: 260px; white-space: pre-wrap; }}
    .actions {{ display: flex; gap: 8px; flex-wrap: wrap; }}
    button {{ background: #2563eb; color: white; border: 0; border-radius: 6px; padding: 9px 12px; cursor: pointer; }}
    button.secondary {{ background: #4b5563; }}
    .badge {{ display: inline-block; padding: 2px 7px; border-radius: 999px; background: #dbeafe; color: #1e40af; font-size: 12px; }}
  </style>
</head>
<body>
  <header>
    <h1>Climate Risk Dashboard</h1>
    <div>Local test console. Dashboard mode previews notifications without pushing LINE.</div>
  </header>
  <main>{body}</main>
</body>
</html>"""


@dashboard_blueprint.get("/dashboard")
def dashboard_home():
    db_path = current_app.config["DB_PATH"]
    users = get_all_users(db_path=db_path)
    risks = get_recent_risk_logs(db_path=db_path)
    previews = get_preview_notifications(db_path=db_path)
    mode = current_app.config["NOTIFICATION_MODE"]

    users_rows = "".join(
        f"<tr><td>{html.escape(user_id)}</td><td>{html.escape(provinces)}</td></tr>"
        for user_id, provinces in users
    ) or "<tr><td colspan='2'>No users yet</td></tr>"

    def _score_bar(score: int) -> str:
        color = SCORE_COLORS.get(score, "#9ca3af")
        label = SCORE_LABELS.get(score, "?")
        pct = score * 20
        return (
            f"<div style='display:flex;align-items:center;gap:6px'>"
            f"<div style='width:{pct}%;min-width:6px;height:14px;background:{color};border-radius:3px'></div>"
            f"<span style='color:{color};font-weight:600;font-size:13px'>{html.escape(label)}</span>"
            f"</div>"
        )

    sorted_risks = sorted(risks, key=lambda r: r["score"], reverse=True)
    risk_rows = "".join(
        "<tr>"
        f"<td>{html.escape(row['province'])}</td>"
        f"<td>{html.escape(row['hazard_type'])}</td>"
        f"<td style='min-width:160px'>{_score_bar(row['score'])}</td>"
        f"<td>{row['raw_value']}</td>"
        f"<td>{html.escape(row['checked_at'])}</td>"
        "</tr>"
        for row in sorted_risks
    ) or "<tr><td colspan='5'>No risk logs yet</td></tr>"

    preview_rows = ""
    for row in previews:
        payload = row["payload_json"]
        payload_pretty = ""
        if payload:
            try:
                payload_pretty = json.dumps(json.loads(payload), ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                payload_pretty = payload
        preview_rows += (
            "<section>"
            f"<div><span class='badge'>{html.escape(row['notification_type'])}</span> "
            f"{html.escape(row['created_at'])}</div>"
            f"<p><strong>User:</strong> {html.escape(row['user_id'])} "
            f"<strong>Province:</strong> {html.escape(row['province'])} "
            f"<strong>Hazard:</strong> {html.escape(row['hazard_type'] or '-')}</p>"
            f"<pre>{html.escape(row['text_preview'])}</pre>"
            + (f"<pre>{html.escape(payload_pretty)}</pre>" if payload_pretty else "")
            + "</section>"
        )
    preview_rows = preview_rows or "<section>No preview notifications yet</section>"

    body = f"""
    <section>
      <h2>Mode: <span class="badge">{html.escape(mode)}</span></h2>
      <div class="actions">
        <form method="post" action="{url_for('dashboard.run_hourly_check')}"><button>Run hourly check</button></form>
        <form method="post" action="{url_for('dashboard.send_daily_summary')}"><button>Send daily summary</button></form>
        <form method="post" action="{url_for('dashboard.clear_previews')}"><button class="secondary">Clear previews</button></form>
      </div>
    </section>
    <section>
      <h2>Test Subscription</h2>
      <form method="post" action="{url_for('dashboard.save_test_subscription')}" class="actions">
        <input name="user_id" value="dashboard-user" aria-label="User ID">
        <input name="provinces" value="เชียงใหม่ กรุงเทพมหานคร" aria-label="Provinces">
        <button>Save test user</button>
      </form>
    </section>
    <section>
      <h2>Users</h2>
      <table><thead><tr><th>User ID</th><th>Provinces</th></tr></thead><tbody>{users_rows}</tbody></table>
    </section>
    <section>
      <h2>Latest Risk Logs</h2>
      <table><thead><tr><th>Province</th><th>Hazard</th><th>Score</th><th>Raw</th><th>Checked At</th></tr></thead><tbody>{risk_rows}</tbody></table>
    </section>
    <section>
      <h2>Notification Previews</h2>
      {preview_rows}
    </section>
    """
    return _page("Climate Risk Dashboard", body)


@dashboard_blueprint.post("/dashboard/users")
def save_test_subscription():
    user_id = request.form.get("user_id", "dashboard-user").strip() or "dashboard-user"
    requested = [p.strip() for p in request.form.get("provinces", "").split() if p.strip()]
    province_map = load_provinces()
    valid = [p for p in requested if p in province_map]
    if valid:
        save_user_provinces(user_id, valid, db_path=current_app.config["DB_PATH"])
    return redirect(url_for("dashboard.dashboard_home"))


@dashboard_blueprint.post("/dashboard/run-hourly-check")
def run_hourly_check():
    current_app.config["HOURLY_CHECK"]()
    return redirect(url_for("dashboard.dashboard_home"))


@dashboard_blueprint.post("/dashboard/send-daily-summary")
def send_daily_summary():
    current_app.config["DAILY_SUMMARY"]()
    return redirect(url_for("dashboard.dashboard_home"))


@dashboard_blueprint.post("/dashboard/clear-preview-notifications")
def clear_previews():
    clear_preview_notifications(db_path=current_app.config["DB_PATH"])
    return redirect(url_for("dashboard.dashboard_home"))
