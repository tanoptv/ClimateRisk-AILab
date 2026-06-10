# Climate Risk Line Bot — Build Guide

ระบบ AI แจ้งเตือนความเสี่ยงภัยธรรมชาติสำหรับประชาชนทั่วไป 77 จังหวัดทั่วไทย

---

## สารบัญ

1. [ภาพรวมระบบ](#1-ภาพรวมระบบ)
2. [สิ่งที่ต้องเตรียม](#2-สิ่งที่ต้องเตรียม)
3. [โครงสร้าง Project](#3-โครงสร้าง-project)
4. [ติดตั้ง Dependencies](#4-ติดตั้ง-dependencies)
5. [ตั้งค่า API Keys](#5-ตั้งค่า-api-keys)
6. [สร้าง Database](#6-สร้าง-database)
7. [สร้าง Fetchers](#7-สร้าง-fetchers)
8. [สร้าง Risk Scorer](#8-สร้าง-risk-scorer)
9. [สร้าง LLM Analyzer](#9-สร้าง-llm-analyzer)
10. [สร้าง Line Bot](#10-สร้าง-line-bot)
11. [สร้าง Main Scheduler](#11-สร้าง-main-scheduler)
12. [รัน ngrok](#12-รัน-ngrok)
13. [ทดสอบระบบ](#13-ทดสอบระบบ)

---

## 1. ภาพรวมระบบ

```
[APIs] ──────► [Fetchers] ──► [Risk Scorer] ──► [LLM Analyzer]
 Open-Meteo      weather.py     score 1–5         Claude Haiku
 OpenAQ          air_quality.py  threshold          อธิบายเหตุผล
 USGS            earthquake.py                         │
 NASA FIRMS      fire.py                               ▼
                                                  [Line Bot]
[APScheduler]                                      Flex Message
 ทุกชั่วโมง ──────────────────────────────────►  Daily 7AM
 emergency ─────────────────────────────────────► Alert score=5
                                                       │
                                                  [SQLite DB]
                                                   users
                                                   risk_log
                                                   alerts_sent
```

### Flow การทำงาน

1. APScheduler ปลุก Fetchers ทุก 1 ชั่วโมง
2. Fetchers ดึงข้อมูลจาก 4 APIs สำหรับ 77 จังหวัด
3. Risk Scorer คำนวณ score 1–5 จาก threshold
4. Claude Haiku รับ score + raw data → อธิบายเป็นภาษาไทย
5. บันทึกผลลงใน SQLite
6. ถ้า score = 5 → ส่ง Emergency Alert ทันที
7. ทุกเช้า 7:00 น. → ส่ง Daily Summary Flex Message

---

## 2. สิ่งที่ต้องเตรียม

### Accounts ที่ต้องสมัคร

| บริการ | ลิงก์สมัคร | ใช้ทำอะไร | ค่าใช้จ่าย |
|--------|-----------|-----------|-----------|
| Anthropic | console.anthropic.com | Claude Haiku API key | มี free credit |
| Line Developers | developers.line.biz | Line Bot Channel | ฟรี |
| NASA FIRMS | firms.modaps.eosdis.nasa.gov/api | ข้อมูลไฟป่า | ฟรี |
| ngrok | ngrok.com | Tunnel localhost | ฟรี |

### Software ที่ต้องติดตั้ง

- Python 3.10+
- ngrok CLI
- Git (optional)

---

## 3. โครงสร้าง Project

```
climate-risk-bot/
├── main.py
├── .env
├── .gitignore
├── requirements.txt
├── data/
│   └── provinces.json       # ข้อมูล lat/lon 77 จังหวัด
├── fetchers/
│   ├── __init__.py
│   ├── weather.py
│   ├── air_quality.py
│   ├── earthquake.py
│   └── fire.py
├── scorer/
│   ├── __init__.py
│   └── risk_scorer.py
├── llm/
│   ├── __init__.py
│   └── analyzer.py
├── bot/
│   ├── __init__.py
│   └── line_bot.py
└── db/
    ├── __init__.py
    └── database.py
```

สร้าง folder structure:

```bash
mkdir climate-risk-bot
cd climate-risk-bot
mkdir fetchers scorer llm bot db data
touch main.py .env .gitignore requirements.txt
touch fetchers/__init__.py fetchers/weather.py fetchers/air_quality.py fetchers/earthquake.py fetchers/fire.py
touch scorer/__init__.py scorer/risk_scorer.py
touch llm/__init__.py llm/analyzer.py
touch bot/__init__.py bot/line_bot.py
touch db/__init__.py db/database.py
```

---

## 4. ติดตั้ง Dependencies

### requirements.txt

```
anthropic==0.40.0
flask==3.1.0
line-bot-sdk==3.14.0
apscheduler==3.10.4
requests==2.32.3
python-dotenv==1.0.1
```

ติดตั้ง:

```bash
pip install -r requirements.txt
```

---

## 5. ตั้งค่า API Keys

### .env

```env
# Anthropic
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxx

# Line Bot
LINE_CHANNEL_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LINE_CHANNEL_ACCESS_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# NASA FIRMS
NASA_FIRMS_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx

# App
PORT=8000
```

### .gitignore

```
.env
*.db
__pycache__/
*.pyc
.DS_Store
```

### วิธีหา API Keys

**Line Bot:**
1. ไปที่ developers.line.biz → Create Provider → Create Channel → Messaging API
2. ในหน้า Channel settings → คัดลอก **Channel secret**
3. ใน Messaging API tab → Issue **Channel access token**

**NASA FIRMS:**
1. ไปที่ firms.modaps.eosdis.nasa.gov/api/
2. กด "Get MAP_KEY" → ลงทะเบียนด้วย email
3. รับ key ทาง email ภายใน 1-2 นาที

---

## 6. สร้าง Database

### db/database.py

```python
import sqlite3
import os
from datetime import datetime

DB_PATH = "climate_risk.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            provinces TEXT,
            created_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS risk_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            province TEXT,
            hazard_type TEXT,
            score INTEGER,
            raw_value REAL,
            explanation TEXT,
            checked_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS alerts_sent (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            province TEXT,
            hazard_type TEXT,
            score INTEGER,
            sent_at TEXT
        )
    """)

    conn.commit()
    conn.close()

def save_user_provinces(user_id: str, provinces: list):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO users (user_id, provinces, created_at)
        VALUES (?, ?, ?)
    """, (user_id, ",".join(provinces), datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_user_provinces(user_id: str) -> list:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT provinces FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row and row[0]:
        return row[0].split(",")
    return []

def get_all_users() -> list:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT user_id, provinces FROM users")
    rows = c.fetchall()
    conn.close()
    return rows

def save_risk_log(province: str, hazard_type: str, score: int,
                  raw_value: float, explanation: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO risk_log (province, hazard_type, score, raw_value, explanation, checked_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (province, hazard_type, score, raw_value, explanation, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_latest_risk(province: str) -> list:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT hazard_type, score, explanation, checked_at
        FROM risk_log
        WHERE province = ?
        ORDER BY checked_at DESC
        LIMIT 6
    """, (province,))
    rows = c.fetchall()
    conn.close()
    return rows

def was_alert_sent_recently(user_id: str, province: str, hazard_type: str,
                             hours: int = 6) -> bool:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT COUNT(*) FROM alerts_sent
        WHERE user_id = ? AND province = ? AND hazard_type = ?
        AND sent_at > datetime('now', ?)
    """, (user_id, province, hazard_type, f"-{hours} hours"))
    count = c.fetchone()[0]
    conn.close()
    return count > 0

def save_alert_sent(user_id: str, province: str, hazard_type: str, score: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO alerts_sent (user_id, province, hazard_type, score, sent_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, province, hazard_type, score, datetime.now().isoformat()))
    conn.commit()
    conn.close()
```

---

## 7. สร้าง Fetchers

### data/provinces.json (ตัวอย่าง 5 จังหวัด — ต้องเพิ่มครบ 77)

```json
{
  "กรุงเทพมหานคร": {"lat": 13.7563, "lon": 100.5018},
  "เชียงใหม่":     {"lat": 18.7883, "lon": 98.9853},
  "ขอนแก่น":       {"lat": 16.4419, "lon": 102.8360},
  "ภูเก็ต":        {"lat": 7.8804,  "lon": 98.3923},
  "สงขลา":         {"lat": 7.1756,  "lon": 100.6135}
}
```

> ดาวน์โหลด provinces.json ครบ 77 จังหวัดได้จาก: github.com/kristw/regionthailand

---

### fetchers/weather.py — Open-Meteo (น้ำท่วม / พายุ / ภัยแล้ง)

```python
import requests

BASE_URL = "https://api.open-meteo.com/v1/forecast"

def fetch_weather(lat: float, lon: float) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "precipitation,wind_speed_10m,et0_fao_evapotranspiration",
        "daily": "precipitation_sum,wind_speed_10m_max",
        "forecast_days": 1,
        "timezone": "Asia/Bangkok"
    }
    try:
        res = requests.get(BASE_URL, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()

        hourly = data.get("hourly", {})
        daily = data.get("daily", {})

        precip_values = hourly.get("precipitation", [0])
        wind_values = hourly.get("wind_speed_10m", [0])

        return {
            "precipitation_max": max(precip_values) if precip_values else 0,
            "precipitation_sum": sum(precip_values) if precip_values else 0,
            "wind_speed_max": max(wind_values) if wind_values else 0,
            "daily_precip_sum": daily.get("precipitation_sum", [0])[0] or 0
        }
    except Exception as e:
        print(f"Weather fetch error: {e}")
        return {"precipitation_max": 0, "precipitation_sum": 0,
                "wind_speed_max": 0, "daily_precip_sum": 0}
```

---

### fetchers/air_quality.py — OpenAQ (PM2.5)

```python
import requests

BASE_URL = "https://api.openaq.org/v2/measurements"

def fetch_pm25(lat: float, lon: float) -> float:
    params = {
        "coordinates": f"{lat},{lon}",
        "radius": 50000,
        "parameter": "pm25",
        "limit": 5,
        "order_by": "datetime",
        "sort": "desc"
    }
    headers = {"Accept": "application/json"}
    try:
        res = requests.get(BASE_URL, params=params, headers=headers, timeout=10)
        res.raise_for_status()
        results = res.json().get("results", [])
        if results:
            values = [r["value"] for r in results if r.get("value") is not None]
            return sum(values) / len(values) if values else 0
        return 0
    except Exception as e:
        print(f"AQ fetch error: {e}")
        return 0
```

---

### fetchers/earthquake.py — USGS

```python
import requests
from datetime import datetime, timedelta

BASE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"

def fetch_earthquake(lat: float, lon: float) -> dict:
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=24)

    params = {
        "format": "geojson",
        "latitude": lat,
        "longitude": lon,
        "maxradiuskm": 300,
        "starttime": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "endtime": end_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "orderby": "magnitude"
    }
    try:
        res = requests.get(BASE_URL, params=params, timeout=10)
        res.raise_for_status()
        features = res.json().get("features", [])

        if not features:
            return {"max_magnitude": 0, "count": 0}

        magnitudes = [f["properties"]["mag"] for f in features
                      if f["properties"].get("mag")]
        return {
            "max_magnitude": max(magnitudes) if magnitudes else 0,
            "count": len(features)
        }
    except Exception as e:
        print(f"Earthquake fetch error: {e}")
        return {"max_magnitude": 0, "count": 0}
```

---

### fetchers/fire.py — NASA FIRMS

```python
import requests
import os
from datetime import datetime, timedelta

def fetch_fire(lat: float, lon: float) -> dict:
    api_key = os.getenv("NASA_FIRMS_API_KEY")
    delta = 0.5  # ~55km radius
    area = f"{lon-delta},{lat-delta},{lon+delta},{lat+delta}"
    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{api_key}/VIIRS_SNPP_NRT/{area}/1"

    try:
        res = requests.get(url, timeout=15)
        if res.status_code != 200 or not res.text.strip():
            return {"fire_count": 0, "max_frp": 0}

        lines = res.text.strip().split("\n")
        if len(lines) <= 1:
            return {"fire_count": 0, "max_frp": 0}

        fire_count = len(lines) - 1
        frp_values = []
        for line in lines[1:]:
            cols = line.split(",")
            try:
                frp_values.append(float(cols[13]))
            except (IndexError, ValueError):
                pass

        return {
            "fire_count": fire_count,
            "max_frp": max(frp_values) if frp_values else 0
        }
    except Exception as e:
        print(f"Fire fetch error: {e}")
        return {"fire_count": 0, "max_frp": 0}
```

---

## 8. สร้าง Risk Scorer

### scorer/risk_scorer.py

```python
def score_flood(weather: dict) -> tuple[int, float]:
    precip = weather.get("precipitation_max", 0)
    if precip >= 50:   return 5, precip
    if precip >= 35:   return 4, precip
    if precip >= 20:   return 3, precip
    if precip >= 10:   return 2, precip
    return 1, precip

def score_pm25(pm25_value: float) -> tuple[int, float]:
    if pm25_value >= 200: return 5, pm25_value
    if pm25_value >= 150: return 4, pm25_value
    if pm25_value >= 100: return 3, pm25_value
    if pm25_value >= 50:  return 2, pm25_value
    return 1, pm25_value

def score_drought(weather: dict) -> tuple[int, float]:
    daily_precip = weather.get("daily_precip_sum", 0)
    if daily_precip == 0:  return 4, daily_precip
    if daily_precip < 1:   return 3, daily_precip
    if daily_precip < 5:   return 2, daily_precip
    return 1, daily_precip

def score_storm(weather: dict) -> tuple[int, float]:
    wind = weather.get("wind_speed_max", 0)
    if wind >= 90:  return 5, wind
    if wind >= 65:  return 4, wind
    if wind >= 40:  return 3, wind
    if wind >= 20:  return 2, wind
    return 1, wind

def score_earthquake(eq: dict) -> tuple[int, float]:
    mag = eq.get("max_magnitude", 0)
    if mag >= 7.0:  return 5, mag
    if mag >= 6.0:  return 4, mag
    if mag >= 5.0:  return 3, mag
    if mag >= 4.0:  return 2, mag
    return 1, mag

def score_fire(fire: dict) -> tuple[int, float]:
    count = fire.get("fire_count", 0)
    frp = fire.get("max_frp", 0)
    if count >= 20 or frp >= 500:  return 5, frp
    if count >= 10 or frp >= 200:  return 4, frp
    if count >= 5  or frp >= 50:   return 3, frp
    if count >= 1:                  return 2, frp
    return 1, frp

HAZARD_LABELS = {
    "flood":      "🌊 น้ำท่วม",
    "pm25":       "💨 ฝุ่น PM2.5",
    "drought":    "☀️ ภัยแล้ง",
    "storm":      "🌀 พายุ",
    "earthquake": "🌍 แผ่นดินไหว",
    "fire":       "🔥 ไฟป่า"
}

def score_all(weather: dict, pm25: float,
              earthquake: dict, fire: dict) -> dict:
    return {
        "flood":      score_flood(weather),
        "pm25":       score_pm25(pm25),
        "drought":    score_drought(weather),
        "storm":      score_storm(weather),
        "earthquake": score_earthquake(earthquake),
        "fire":       score_fire(fire)
    }
```

---

## 9. สร้าง LLM Analyzer

### llm/analyzer.py

```python
import anthropic
import os

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

HAZARD_TH = {
    "flood": "น้ำท่วม",
    "pm25": "ฝุ่น PM2.5",
    "drought": "ภัยแล้ง",
    "storm": "พายุ",
    "earthquake": "แผ่นดินไหว",
    "fire": "ไฟป่า"
}

def analyze_risk(province: str, hazard_type: str,
                 score: int, raw_value: float) -> str:
    if score <= 1:
        return "สถานการณ์ปกติ ไม่มีความเสี่ยงในขณะนี้"

    hazard_th = HAZARD_TH.get(hazard_type, hazard_type)

    prompt = f"""คุณคือผู้เชี่ยวชาญด้านภัยธรรมชาติของประเทศไทย
ให้ข้อมูลสั้นกระชับ 2-3 ประโยค เป็นภาษาไทย

จังหวัด: {province}
ประเภทภัย: {hazard_th}
ระดับความเสี่ยง: {score}/5
ค่าที่วัดได้: {raw_value:.1f}

อธิบาย: 1) ทำไมถึงได้คะแนนนี้ 2) ผลกระทบที่อาจเกิดขึ้น 3) ประชาชนควรทำอะไร
ห้ามขึ้นต้นด้วย "จากข้อมูล" หรือ "ตามที่"
"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text.strip()
```

---

## 10. สร้าง Line Bot

### bot/line_bot.py

```python
import os
import json
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest, PushMessageRequest,
    TextMessage, FlexMessage, FlexContainer
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from db.database import save_user_provinces, get_user_provinces

app = Flask(__name__)

configuration = Configuration(
    access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
)
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        if text.startswith("/ติดตาม"):
            provinces = text.replace("/ติดตาม", "").strip().split()
            if provinces:
                save_user_provinces(user_id, provinces)
                reply = f"✅ ติดตามแล้ว: {', '.join(provinces)}\nจะได้รับรายงานทุกเช้า 07:00 น."
            else:
                reply = "กรุณาระบุชื่อจังหวัด เช่น /ติดตาม เชียงใหม่ กรุงเทพมหานคร"

        elif text == "/จังหวัดของฉัน":
            provinces = get_user_provinces(user_id)
            reply = f"📍 จังหวัดที่ติดตาม: {', '.join(provinces)}" if provinces else "ยังไม่ได้ติดตามจังหวัดใด"

        elif text == "/ช่วยเหลือ":
            reply = ("คำสั่งที่ใช้ได้:\n"
                     "/ติดตาม [จังหวัด] — เพิ่มจังหวัดที่ต้องการติดตาม\n"
                     "/จังหวัดของฉัน — ดูจังหวัดที่ติดตามอยู่\n"
                     "รายงานจะส่งทุกเช้า 07:00 น.")
        else:
            reply = "พิมพ์ /ช่วยเหลือ เพื่อดูคำสั่งทั้งหมด"

        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply)]
            )
        )

def send_flex_message(user_id: str, province: str, risks: list):
    """
    risks = [{"hazard": "flood", "label": "🌊 น้ำท่วม", "score": 3, "explanation": "..."}]
    """
    score_colors = {1: "#4ade80", 2: "#a3e635", 3: "#facc15", 4: "#fb923c", 5: "#ef4444"}
    score_labels = {1: "ปกติ", 2: "เฝ้าระวัง", 3: "ระวัง", 4: "อันตราย", 5: "วิกฤต"}

    contents = []
    for r in risks:
        score = r["score"]
        bar_width = f"{score * 20}%"
        contents.append({
            "type": "box",
            "layout": "vertical",
            "margin": "md",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": r["label"],
                         "size": "sm", "color": "#ffffff", "flex": 3},
                        {"type": "text",
                         "text": f"{score}/5 {score_labels[score]}",
                         "size": "sm", "color": score_colors[score],
                         "align": "end", "flex": 2}
                    ]
                },
                {
                    "type": "box", "layout": "horizontal",
                    "height": "6px", "margin": "sm",
                    "backgroundColor": "#333333", "cornerRadius": "3px",
                    "contents": [{
                        "type": "box", "layout": "vertical",
                        "backgroundColor": score_colors[score],
                        "cornerRadius": "3px",
                        "width": bar_width, "contents": []
                    }]
                },
                {
                    "type": "text", "text": r["explanation"],
                    "size": "xs", "color": "#aaaaaa",
                    "wrap": True, "margin": "sm"
                }
            ]
        })

    flex_body = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#1a1a2e",
            "paddingAll": "20px",
            "contents": [
                {
                    "type": "text",
                    "text": f"📊 รายงานความเสี่ยง",
                    "color": "#a78bfa", "size": "xs", "weight": "bold"
                },
                {
                    "type": "text", "text": province,
                    "color": "#ffffff", "size": "xl",
                    "weight": "bold", "margin": "sm"
                },
                {"type": "separator", "margin": "md", "color": "#333333"},
                *contents
            ]
        }
    }

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.push_message(
            PushMessageRequest(
                to=user_id,
                messages=[FlexMessage(
                    alt_text=f"รายงานความเสี่ยง {province}",
                    contents=FlexContainer.from_dict(flex_body)
                )]
            )
        )

def send_emergency_alert(user_id: str, province: str,
                          hazard_label: str, score: int, explanation: str):
    message = (f"🚨 แจ้งเตือนฉุกเฉิน!\n\n"
               f"📍 {province}\n"
               f"{hazard_label} — ระดับ {score}/5 (วิกฤต)\n\n"
               f"{explanation}")

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.push_message(
            PushMessageRequest(
                to=user_id,
                messages=[TextMessage(text=message)]
            )
        )
```

---

## 11. สร้าง Main Scheduler

### main.py

```python
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

load_dotenv()

from db.database import (init_db, get_all_users, save_risk_log,
                          was_alert_sent_recently, save_alert_sent,
                          get_latest_risk)
from fetchers.weather import fetch_weather
from fetchers.air_quality import fetch_pm25
from fetchers.earthquake import fetch_earthquake
from fetchers.fire import fetch_fire
from scorer.risk_scorer import score_all, HAZARD_LABELS
from llm.analyzer import analyze_risk
from bot.line_bot import app, send_flex_message, send_emergency_alert

with open("data/provinces.json", "r", encoding="utf-8") as f:
    PROVINCES = json.load(f)

def check_risks_for_province(province: str, coords: dict) -> list:
    lat, lon = coords["lat"], coords["lon"]

    weather    = fetch_weather(lat, lon)
    pm25       = fetch_pm25(lat, lon)
    earthquake = fetch_earthquake(lat, lon)
    fire       = fetch_fire(lat, lon)

    scores = score_all(weather, pm25, earthquake, fire)
    results = []

    for hazard, (score, raw_value) in scores.items():
        explanation = analyze_risk(province, hazard, score, raw_value)
        save_risk_log(province, hazard, score, raw_value, explanation)
        results.append({
            "hazard":      hazard,
            "label":       HAZARD_LABELS[hazard],
            "score":       score,
            "raw_value":   raw_value,
            "explanation": explanation
        })

    return results

def hourly_check():
    print(f"[{datetime.now().strftime('%H:%M')}] Running hourly check...")
    users = get_all_users()

    watched_provinces = set()
    user_province_map = {}
    for user_id, provinces_str in users:
        provinces = provinces_str.split(",") if provinces_str else []
        for p in provinces:
            watched_provinces.add(p.strip())
        user_province_map[user_id] = [p.strip() for p in provinces]

    risk_cache = {}
    for province in watched_provinces:
        if province in PROVINCES:
            risk_cache[province] = check_risks_for_province(
                province, PROVINCES[province]
            )

    for user_id, provinces in user_province_map.items():
        for province in provinces:
            risks = risk_cache.get(province, [])
            for r in risks:
                if r["score"] == 5:
                    if not was_alert_sent_recently(user_id, province, r["hazard"]):
                        send_emergency_alert(
                            user_id, province,
                            r["label"], r["score"], r["explanation"]
                        )
                        save_alert_sent(user_id, province, r["hazard"], r["score"])
                        print(f"  🚨 Emergency sent: {province} {r['hazard']}")

def daily_summary():
    print(f"[{datetime.now().strftime('%H:%M')}] Sending daily summaries...")
    users = get_all_users()

    for user_id, provinces_str in users:
        provinces = provinces_str.split(",") if provinces_str else []
        for province in provinces:
            province = province.strip()
            risks = get_latest_risk(province)
            if not risks:
                continue

            formatted = []
            for hazard_type, score, explanation, _ in risks:
                formatted.append({
                    "hazard":      hazard_type,
                    "label":       HAZARD_LABELS.get(hazard_type, hazard_type),
                    "score":       score,
                    "explanation": explanation
                })

            send_flex_message(user_id, province, formatted)
            print(f"  📊 Daily sent: {user_id} — {province}")

if __name__ == "__main__":
    init_db()
    print("✅ Database initialized")

    scheduler = BackgroundScheduler(timezone="Asia/Bangkok")
    scheduler.add_job(hourly_check, "interval", hours=1, id="hourly_check")
    scheduler.add_job(daily_summary, CronTrigger(hour=7, minute=0), id="daily_summary")
    scheduler.start()
    print("✅ Scheduler started")
    print("   - Hourly check: every hour")
    print("   - Daily summary: 07:00 AM")

    hourly_check()

    port = int(os.getenv("PORT", 8000))
    print(f"✅ Line Bot webhook running on port {port}")
    app.run(host="0.0.0.0", port=port)
```

---

## 12. รัน ngrok

### ขั้นตอน

เปิด Terminal แรก (รัน Bot):

```bash
cd climate-risk-bot
python main.py
```

เปิด Terminal ที่สอง (รัน ngrok):

```bash
ngrok http 8000
```

ngrok จะแสดง URL เช่น:

```
Forwarding   https://abc123.ngrok-free.app -> http://localhost:8000
```

### ตั้งค่า Webhook ใน Line Developers

1. ไปที่ developers.line.biz → เลือก Channel
2. Messaging API tab → Webhook settings
3. ใส่ Webhook URL: `https://abc123.ngrok-free.app/callback`
4. กด **Verify** → ต้องขึ้น Success
5. เปิด **Use webhook**

---

## 13. ทดสอบระบบ

### ทดสอบ Fetchers

```python
# test_fetch.py
from fetchers.weather import fetch_weather
from fetchers.air_quality import fetch_pm25
from fetchers.earthquake import fetch_earthquake
from fetchers.fire import fetch_fire

# เชียงใหม่
lat, lon = 18.7883, 98.9853

print("Weather:", fetch_weather(lat, lon))
print("PM2.5:", fetch_pm25(lat, lon))
print("Earthquake:", fetch_earthquake(lat, lon))
print("Fire:", fetch_fire(lat, lon))
```

```bash
python test_fetch.py
```

### ทดสอบ Risk Scorer

```python
# test_score.py
from scorer.risk_scorer import score_all

weather    = {"precipitation_max": 25, "precipitation_sum": 40,
              "wind_speed_max": 15, "daily_precip_sum": 0.5}
pm25       = 120.0
earthquake = {"max_magnitude": 3.5, "count": 1}
fire       = {"fire_count": 3, "max_frp": 80}

results = score_all(weather, pm25, earthquake, fire)
for hazard, (score, value) in results.items():
    print(f"{hazard}: {score}/5 (value={value:.1f})")
```

### ทดสอบ Claude Haiku

```python
# test_llm.py
from llm.analyzer import analyze_risk

result = analyze_risk("เชียงใหม่", "pm25", 4, 165.0)
print(result)
```

### ทดสอบ Line Bot ด้วยการ chat

เปิด Line แล้วส่งข้อความให้ Bot:

```
/ติดตาม เชียงใหม่
/จังหวัดของฉัน
/ช่วยเหลือ
```

---

## Risk Score Reference

| Score | ระดับ | สีแสดง | การแจ้งเตือน |
|-------|-------|--------|------------|
| 1 | ปกติ | 🟢 เขียว | ไม่แจ้ง |
| 2 | เฝ้าระวัง | 🟡 เหลืองอ่อน | ใน Daily Summary |
| 3 | ระวัง | 🟠 ส้มอ่อน | ใน Daily Summary |
| 4 | อันตราย | 🔴 ส้มแดง | ใน Daily Summary |
| 5 | วิกฤต | 🚨 แดง | **Emergency Alert ทันที** |

## Threshold Reference

| ภัย | Score 2 | Score 3 | Score 4 | Score 5 |
|-----|---------|---------|---------|---------|
| น้ำท่วม (mm/hr) | ≥10 | ≥20 | ≥35 | ≥50 |
| PM2.5 (μg/m³) | ≥50 | ≥100 | ≥150 | ≥200 |
| พายุ (km/h) | ≥20 | ≥40 | ≥65 | ≥90 |
| แผ่นดินไหว (Mw) | ≥4.0 | ≥5.0 | ≥6.0 | ≥7.0 |
| ไฟป่า (จุด) | ≥1 | ≥5 | ≥10 | ≥20 |
| ภัยแล้ง (mm/day) | <5 | <1 | =0 | — |
