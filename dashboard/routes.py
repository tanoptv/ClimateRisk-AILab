import html
import json
from datetime import datetime, timezone, timedelta

from flask import Blueprint, current_app, redirect, url_for
from flask import request

_BKK = timezone(timedelta(hours=7))


def _to_bkk(utc_iso: str) -> str:
    try:
        dt = datetime.fromisoformat(utc_iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(_BKK).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return utc_iso

from scorer.risk_scorer import HAZARD_LABELS, SCORE_COLORS, SCORE_LABELS
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
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
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


def _render_map(risks: list, provinces: dict) -> str:
    province_score: dict[str, int] = {}
    province_rows: dict[str, list] = {}
    for row in risks:
        p = row["province"]
        s = int(row["score"])
        if s > province_score.get(p, 0):
            province_score[p] = s
        province_rows.setdefault(p, []).append(row)

    markers_data = []
    for name, coords in provinces.items():
        score = province_score.get(name, 0)
        rows = sorted(province_rows.get(name, []), key=lambda x: int(x["score"]), reverse=True)
        detail = "".join(
            f"{HAZARD_LABELS.get(r['hazard_type'], r['hazard_type'])}: "
            f"{SCORE_LABELS.get(int(r['score']), '?')} ({r['score']}/5)<br>"
            for r in rows
        ) or "ยังไม่มีข้อมูล"
        markers_data.append({
            "name": name,
            "lat": coords["lat"],
            "lon": coords["lon"],
            "score": score,
            "popup": f"<strong>{name}</strong><br><small>{detail}</small>",
        })

    markers_json = json.dumps(markers_data, ensure_ascii=False)
    colors_json = json.dumps(SCORE_COLORS)

    js = (
        "(function() {"
        "  var COLORS = " + colors_json + ";"
        "  var markers = " + markers_json + ";"
        "  var map = L.map('risk-map').setView([13.0, 101.0], 6);"
        "  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {"
        "    attribution: '&copy; <a href=\"https://www.openstreetmap.org/copyright\">OpenStreetMap</a>'"
        "  }).addTo(map);"
        "  markers.forEach(function(m) {"
        "    L.circleMarker([m.lat, m.lon], {"
        "      radius: 9, fillColor: COLORS[m.score] || '#9ca3af',"
        "      color: '#fff', weight: 1.5, opacity: 1, fillOpacity: 0.9"
        "    }).addTo(map)"
        "    .bindPopup(m.popup)"
        "    .bindTooltip(m.name, {permanent: false, direction: 'top', className: 'prov-tip'});"
        "  });"
        "})();"
    )

    legend_html = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:4px;margin-right:10px;font-size:12px">'
        f'<span style="width:13px;height:13px;border-radius:50%;background:{color};display:inline-block;'
        f'border:2px solid #fff;box-shadow:0 0 0 1px #ccc"></span>'
        f'{html.escape(SCORE_LABELS[score])}</span>'
        for score, color in SCORE_COLORS.items()
    )

    tracked = len(province_score)
    total = len(provinces)
    return (
        '<div id="risk-map" style="height:540px;border-radius:8px;border:1px solid #bfdbfe"></div>'
        f'<div style="margin-top:8px;display:flex;flex-wrap:wrap;gap:2px 0">{legend_html}</div>'
        f'<p style="font-size:11px;color:#9ca3af;margin:4px 0 0">'
        f'มีข้อมูล {tracked}/{total} จังหวัด · hover = ชื่อจังหวัด · คลิก = รายละเอียด</p>'
        '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>'
        '<script>' + js + '</script>'
    )


def _province_select(all_provinces: dict) -> str:
    names_json = json.dumps(sorted(all_provinces.keys()), ensure_ascii=False)
    js_template = r"""(function(){
var ALL=NAMES_DATA,sel=[],
si=document.getElementById('prov-search'),
dd=document.getElementById('prov-dropdown'),
tg=document.getElementById('prov-tags'),
hd=document.getElementById('prov-hidden');
function syncH(){
  hd.innerHTML='';
  sel.forEach(function(p){
    var i=document.createElement('input');
    i.type='hidden';i.name='provinces';i.value=p;
    hd.appendChild(i);
  });
}
function renderTags(){
  tg.innerHTML='';
  sel.forEach(function(p){
    var t=document.createElement('span');
    t.style.cssText='display:inline-flex;align-items:center;gap:4px;background:#dbeafe;color:#1e40af;padding:3px 10px;border-radius:999px;font-size:13px';
    t.appendChild(document.createTextNode(p));
    var b=document.createElement('button');
    b.type='button';b.innerHTML='&times;';
    b.style.cssText='background:none;border:none;color:#1e40af;cursor:pointer;padding:0 0 0 4px;font-size:16px;line-height:1';
    (function(name){b.onclick=function(){
      sel=sel.filter(function(x){return x!==name;});
      renderTags();syncH();renderDropdown(si.value);
    };})(p);
    t.appendChild(b);tg.appendChild(t);
  });
}
function renderDropdown(q){
  var lq=q.toLowerCase(),f=ALL.filter(function(p){
    return(q===''||p.toLowerCase().indexOf(lq)!==-1)&&sel.indexOf(p)===-1;
  });
  if(!f.length){dd.style.display='none';return;}
  dd.innerHTML='';
  f.slice(0,20).forEach(function(p){
    var item=document.createElement('div');
    item.textContent=p;
    item.style.cssText='padding:8px 12px;cursor:pointer;font-size:14px';
    item.onmouseenter=function(){this.style.background='#f3f4f6';};
    item.onmouseleave=function(){this.style.background='';};
    item.onmousedown=function(e){
      e.preventDefault();
      sel.push(p);si.value='';dd.style.display='none';
      renderTags();syncH();
    };
    dd.appendChild(item);
  });
  dd.style.display='block';
}
si.oninput=function(){renderDropdown(this.value);};
si.onfocus=function(){renderDropdown(this.value);};
document.addEventListener('click',function(e){
  if(!si.contains(e.target)&&!dd.contains(e.target))dd.style.display='none';
});
})();"""
    js = js_template.replace("NAMES_DATA", names_json)
    return (
        '<div style="margin-top:10px">'
        '<div id="prov-tags" style="display:flex;flex-wrap:wrap;gap:4px;min-height:30px;margin-bottom:8px"></div>'
        '<div style="position:relative;display:inline-block">'
        '<input type="text" id="prov-search" placeholder="พิมพ์ชื่อจังหวัด..." autocomplete="off" '
        'style="padding:7px 10px;border:1px solid #d1d5db;border-radius:6px;width:240px;font-size:14px">'
        '<div id="prov-dropdown" style="position:absolute;top:calc(100% + 2px);left:0;'
        'background:white;border:1px solid #d1d5db;border-radius:6px;max-height:220px;overflow-y:auto;'
        'width:260px;display:none;z-index:1000;box-shadow:0 4px 12px rgba(0,0,0,0.12)"></div>'
        '</div>'
        '<p style="font-size:11px;color:#6b7280;margin:6px 0 0">คลิก → พิมพ์ค้นหา → คลิกจังหวัดที่ต้องการ</p>'
        '<div id="prov-hidden"></div>'
        '</div>'
        '<script>' + js + '</script>'
    )


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

    province_map = load_provinces()
    map_html = _render_map(risks, province_map)
    province_select_html = _province_select(province_map)

    sorted_risks = sorted(risks, key=lambda r: r["score"], reverse=True)
    risk_rows = "".join(
        "<tr>"
        f"<td>{html.escape(row['province'])}</td>"
        f"<td>{html.escape(row['hazard_type'])}</td>"
        f"<td style='min-width:160px'>{_score_bar(row['score'])}</td>"
        f"<td>{row['raw_value']}</td>"
        f"<td>{html.escape(_to_bkk(row['checked_at']))}</td>"
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
            f"{html.escape(_to_bkk(row['created_at']))}</div>"
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
      <h2>Test Subscription</h2>
      <form method="post" action="{url_for('dashboard.save_test_subscription')}">
        <div class="actions">
          <input name="user_id" value="dashboard-user" aria-label="User ID"
            style="padding:7px 10px;border:1px solid #d1d5db;border-radius:6px">
          <button type="submit">Save test user</button>
        </div>
        {province_select_html}
      </form>
    </section>
    <section>
      <h2>Mode: <span class="badge">{html.escape(mode)}</span></h2>
      <div class="actions">
        <form method="post" action="{url_for('dashboard.run_hourly_check')}"><button>Run hourly check</button></form>
        <form method="post" action="{url_for('dashboard.send_daily_summary')}"><button>Send daily summary</button></form>
      </div>
    </section>
    <section>
      <h2>Users</h2>
      <table><thead><tr><th>User ID</th><th>Provinces</th></tr></thead><tbody>{users_rows}</tbody></table>
    </section>
    <section>
      <h2>Risk Map</h2>
      {map_html}
    </section>
    <section>
      <h2>Latest Risk Logs</h2>
      <table><thead><tr><th>Province</th><th>Hazard</th><th>Score</th><th>Raw</th><th>Checked At</th></tr></thead><tbody>{risk_rows}</tbody></table>
    </section>
    <section>
      <h2>Notification Previews</h2>
      <div class="actions" style="margin-bottom:12px">
        <form method="post" action="{url_for('dashboard.clear_previews')}">
          <button class="secondary" type="submit">Clear previews</button>
        </form>
      </div>
      {preview_rows}
    </section>
    """
    return _page("Climate Risk Dashboard", body)


@dashboard_blueprint.post("/dashboard/users")
def save_test_subscription():
    user_id = request.form.get("user_id", "dashboard-user").strip() or "dashboard-user"
    requested = [p.strip() for p in request.form.getlist("provinces") if p.strip()]
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
