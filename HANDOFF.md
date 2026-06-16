# HANDOFF — Climate Risk Line Bot

วันที่ส่งต่อ: 2026-06-16
Repo: https://github.com/tanoptv/ClimateRisk-AILab
Live (Vercel): https://climate-risk-ai-4bind9iow-top-tanopt-s-projects.vercel.app/dashboard

อ่านไฟล์นี้ก่อน แล้วดู [README.md](README.md) สำหรับวิธี run/test, [PRD.md](PRD.md) สำหรับ requirements, [build-guide.md](build-guide.md) สำหรับ code ทุก module แบบละเอียด

---

## 1. โปรเจกต์นี้คืออะไร

ระบบแจ้งเตือนความเสี่ยงภัยธรรมชาติ 6 ประเภท (น้ำท่วม, PM2.5, ภัยแล้ง, พายุ, แผ่นดินไหว, ไฟป่า) ครอบคลุม 77 จังหวัดของไทย ผ่าน LINE Bot โดยใช้ Claude Haiku อธิบายผลเป็นภาษาไทย

**สถานะ**: ใช้งานได้ใน "dashboard mode" — ทดสอบทุกอย่างผ่านเว็บ ไม่ต้องมี LINE จริงก็รันได้ครบ

## 2. สิ่งที่ทำเสร็จแล้ว

- โครงสร้างโปรเจกต์ตาม layer: `fetchers/ scorer/ llm/ bot/ db/ dashboard/`
- 6 hazard scorers พร้อม threshold (`scorer/risk_scorer.py`)
- Fetchers: weather (Open-Meteo), PM2.5 (Open-Meteo Air Quality — **ไม่ใช่ OpenAQ แล้ว เพราะ v2 ถูกปิด, v3 ต้องใช้ key**), earthquake (USGS), fire (NASA FIRMS)
- Claude Haiku integration — เรียกเฉพาะ score ≥ 2, score ≤ 1 ใช้ข้อความ hardcode (ประหยัด token)
- SQLite: 4 tables (`users`, `risk_log`, `alerts_sent`, `preview_notifications`)
- Dashboard UI (`/dashboard`) — ดูผล, run hourly check manual, ดู notification preview
- LINE webhook (`bot/line_bot.py`) — ยังไม่ได้ทดสอบกับ LINE จริง (ต้องมี channel key)
- Deploy ขึ้น Vercel ได้แล้ว (ดูข้อ 4 — มีข้อจำกัด)
- Test ทั้งหมด 19 เคส ผ่านหมด (`pytest`)

## 3. สิ่งที่ยังไม่ทำ / ควรทำต่อ

- [ ] **ทดสอบกับ LINE จริง** — ต้องสร้าง LINE Official Account + Messaging API channel, เอา `LINE_CHANNEL_SECRET`/`LINE_CHANNEL_ACCESS_TOKEN` มาใส่ `.env`, ตั้ง `NOTIFICATION_MODE=line`
- [ ] **Scheduler บน production ยังไม่ทำงานจริง** — ดูข้อ 4
- [ ] **NASA FIRMS API key** ยังไม่ได้ใส่ค่าจริง (สมัครฟรีที่ firms.modaps.eosdis.nasa.gov/api/map_key/)
- [ ] ปุ่ม clear ใน dashboard เพิ่งย้ายตำแหน่งแล้ว แต่ยังไม่มี clear สำหรับ "Latest Risk Logs" (ตอนนี้มีแต่ clear "Notification Previews") — ถ้าต้องการเพิ่มก็ทำได้ง่าย ไม่จำเป็นต้องมี เพราะไม่กิน token
- [ ] พิจารณาย้ายไป Railway/Render ถ้าต้องการ auto scheduler จริง (ดูข้อ 4)

## 4. ⚠️ ข้อจำกัดสำคัญบน Vercel (ต้องรู้ก่อนทำต่อ)

Vercel เป็น serverless — ไม่เหมาะกับสถาปัตยกรรมเดิมที่ใช้ APScheduler + SQLite แบบ persistent:

| ส่วน | สถานะบน Vercel |
|---|---|
| Dashboard UI | ✅ ใช้งานได้ปกติ |
| ปุ่ม "Run hourly check" (manual) | ✅ ใช้งานได้ |
| **Auto scheduler** (ทุกชั่วโมง + 7AM cron) | ❌ ไม่ทำงาน — serverless function ไม่มี background process |
| SQLite data | ⚠️ เก็บที่ `/tmp` — หายเมื่อ cold start (ดู `app_config.py` ที่ auto-detect `VERCEL` env แล้วสับ path) |

**ถ้าต้องการให้ auto-scheduler ทำงานจริง** มี 2 ทางเลือก:
1. **ย้ายไป Railway/Render** (แนะนำ, ไม่ต้องแก้โค้ด) — รองรับ long-running process + volume สำหรับ SQLite
2. **อยู่ Vercel ต่อ** แต่ต้องเปลี่ยน SQLite → Postgres (เช่น Neon ฟรี) และเปลี่ยน APScheduler → Vercel Cron Jobs (`vercel.json` มี `crons` field, แต่ schedule ที่ถี่กว่า 1 ครั้ง/วันต้องใช้ Pro plan)

## 5. Environment Variables ที่ต้องมี

ดู `.env.example` ครบ ค่าที่ critical:

```
ANTHROPIC_API_KEY=        # ต้องมีเพื่อให้ Claude วิเคราะห์ความเสี่ยง (score≥2)
NOTIFICATION_MODE=dashboard   # เปลี่ยนเป็น "line" เมื่อพร้อมต่อ LINE จริง
```

**Key เก่าถูก revoke แล้ว** (เคย hardcode หลุดเข้า git history ไปรอบหนึ่ง ดูใน git log commit ก่อน `e07b5f4` — ถูก amend ออกไปแล้วก่อน push แต่ key ตัวนั้นถูกขอให้ rotate ไปแล้ว) — ใครรับงานต่อต้องขอ key ใหม่จากเจ้าของบัญชี Anthropic เอง อย่า hardcode ค่า key ลงโค้ดอีก ใส่ผ่าน `.env` หรือ Vercel Environment Variables เท่านั้น

## 6. วิธี Run/Test ในเครื่อง

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# กรอก ANTHROPIC_API_KEY ใน .env
python main.py
```

เปิด `http://localhost:8000/dashboard` → กด **Save test user** → **Run hourly check** → ดูผลใน Latest Risk Logs

```bash
pytest -q   # ต้องผ่านทั้ง 19 เคส
```

## 7. ไฟล์อ้างอิงอื่นๆ ในโปรเจกต์

- [PRD.md](PRD.md) — Requirements แบบละเอียด, user stories 27 ข้อ
- [build-guide.md](build-guide.md) — code เต็มของทุก module พร้อมคำอธิบาย
- [SPEC.md](SPEC.md) / [TASKS.md](TASKS.md) — checklist การ implement แต่ละ phase
- [presentation.html](presentation.html) — สไลด์ที่ใช้ present รวม Q&A ตอน grill-me interview
