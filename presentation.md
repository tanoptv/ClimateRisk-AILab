# Climate Risk Line Bot
### ระบบ AI แจ้งเตือนความเสี่ยงภัยธรรมชาติสำหรับประชาชนทั่วไป

`🇹🇭 77 จังหวัด` `⚠️ 6 ประเภทภัย` `🤖 Claude Haiku 4.5` `💬 Line Bot` `🐍 Python`

---

## Requirement Gathering — Grill-Me Interview Session

> AI ถามทีละข้อเพื่อ get requirement ก่อนเริ่ม build — ทุกคำตอบกลายเป็น design decision ที่ชัดเจน

### Q1–Q9

| # | คำถาม | ตัวเลือก | คำตอบ |
|---|--------|----------|--------|
| Q1 | ผู้ใช้คือใคร? | ธุรกิจ / นักวิเคราะห์ / ประชาชน | ✅ ประชาชนทั่วไป |
| Q2 | ได้ประโยชน์อะไร? | รู้ความเสี่ยง / ติดข่าว ESG / ราคาสินค้า | ✅ รู้ความเสี่ยงในพื้นที่ตัวเอง |
| Q3 | ครอบคลุมพื้นที่ไหน? | บางภาค / ทั้งไทย / ทั่วโลก | ✅ ทั้งประเทศ 77 จังหวัด |
| Q4 | ประเภทภัยอะไรบ้าง? | 3 ประเภท / 6 ประเภท / ประเภทเดียว | ✅ 6 ประเภท (น้ำท่วม, PM2.5, ภัยแล้ง, พายุ, แผ่นดินไหว, ไฟป่า) |
| Q5 | ข้อมูลจาก API ไหน? | Free APIs / Paid APIs / API ไทย | ✅ Free APIs ทั้งหมด |
| Q6 | ทำงานบ่อยแค่ไหน? | รายสัปดาห์ / รายวัน / real-time | ✅ Real-time ทุกชั่วโมง |
| Q7 | ส่งผลลัพธ์ที่ไหน? | Line / Web dashboard / Telegram / Email | ✅ Line Bot |
| Q8 | Scheduler อะไร? | APScheduler / cron / FastAPI | ✅ APScheduler |
| Q9 | ใช้ LLM ตัวไหน? | Claude / GPT / Gemini / Local | ✅ Claude Haiku 4.5 |

### Q10–Q18

| # | คำถาม | ตัวเลือก | คำตอบ |
|---|--------|----------|--------|
| Q10 | Risk scoring ยังไง? | LLM ตัดสินเอง / threshold แข็ง / ผสม | ✅ Hybrid: code + LLM อธิบาย |
| Q11 | ส่ง notification เมื่อไหร่? | ทุกชั่วโมง / เฉพาะ score≥3 / daily+emergency | ✅ Daily 7AM + ฉุกเฉินเมื่อ score=5 |
| Q12 | เลือกจังหวัดยังไง? | พิมพ์ใน Line / web UI / monitor ทุกจังหวัด | ✅ พิมพ์ชื่อจังหวัดใน Line chat |
| Q13 | เก็บข้อมูลที่ไหน? | SQLite / PostgreSQL / JSON file | ✅ SQLite |
| Q14 | Deploy ที่ไหน? | Local / Cloud VM / Raspberry Pi | ✅ Local machine |
| Q15 | โครงสร้าง project? | Layer-based / hazard-based / ไฟล์เดียว | ✅ Layer-based (fetchers/scorer/llm/bot/db) |
| Q16 | Line webhook ยังไง? | ngrok / cloud deploy / polling | ✅ ngrok tunnel |
| Q17 | Message format? | plain text / Flex Message / รูปภาพ | ✅ Line Flex Message |
| Q18 | Config management? | .env file / config.py / OS env vars | ✅ .env + python-dotenv |

---

## Imagine Your Prototype

### 01 — What kind of task do you need help with?

**การติดตามและประเมินความเสี่ยงภัยธรรมชาติ**

ปัจจุบันถ้าอยากรู้ว่าจังหวัดตัวเองเสี่ยงน้ำท่วม, ฝุ่น PM2.5, หรือไฟป่าไหม ต้องเปิดหลายเว็บไซต์ (กรมอุตุ, AirVisual, กรมอุทกศาสตร์) แล้วตีความเองว่าอันตรายแค่ไหน

| ปัญหาปัจจุบัน | โซลูชัน |
|--------------|---------|
| ❌ ต้องเปิดหลายเว็บ 4+ แหล่ง | ✅ รวมข้อมูลจาก 4 APIs ในที่เดียว |
| ❌ ตีความข้อมูลเองว่าอันตรายแค่ไหน | ✅ AI ให้คะแนนความเสี่ยง 1–5 พร้อมเหตุผล |
| ❌ ไม่มีการแจ้งเตือนเชิงรุก | ✅ แจ้งเตือนอัตโนมัติเข้า Line |
| ❌ ข้อมูลกระจัดกระจาย ไม่มีจุดรวม | ✅ ครอบคลุมทั้ง 77 จังหวัดทั่วไทย |

---

### 02 — What in your day-to-day could be simpler?

**การรู้ว่าวันนี้ควรระวังอะไร**

แทนที่จะต้องไปหาข้อมูลเอง ระบบควรส่งสรุปมาให้ทุกเช้าใน Line ที่ใช้อยู่แล้ว พร้อม risk score 1–5 ที่เข้าใจได้ทันทีโดยไม่ต้องตีความ

| Before | After |
|--------|-------|
| เปิด AirVisual | 07:00 น. — Line ส่งสรุปมาให้เลย |
| → เปิดกรมอุตุนิยมวิทยา | → ดูคะแนน 1–5 ทันที |
| → เปิดกรมอุทกศาสตร์ | → AI อธิบายว่าทำไมถึงเสี่ยง |
| → ตีความเองว่าเสี่ยงไหม | → รู้ว่าควรทำอะไร เตรียมอะไร |
| → ไม่มีใครบอกให้เตรียมตัว | → ไม่ต้องหาข้อมูลเอง |

---

### 03 — Which repetitive bits could be automated?

- 🔄 **ดึงข้อมูลทุกชั่วโมง** — Open-Meteo, OpenAQ, USGS, NASA FIRMS ทำงานอัตโนมัติตลอด 24 ชม.
- 📊 **คำนวณ Risk Score 1–5** — Code ตรวจ threshold อัตโนมัติ → Claude Haiku อธิบายเหตุผลและบริบท
- 🌅 **ส่ง Daily Summary 07:00 น.** — สรุปทุกจังหวัดที่ติดตามเป็น Line Flex Message ทุกเช้า
- 🚨 **Emergency Alert ทันที** — เมื่อ Risk Score = 5 (วิกฤต) แจ้งเตือนฉุกเฉินเข้า Line ทันที ไม่รอรายงานรายวัน

---

### 04 — How would you describe the idea clearly?

> "Line Bot ที่ดึงข้อมูลภัยธรรมชาติจาก 4 API ทุกชั่วโมง ให้ AI วิเคราะห์และให้คะแนนความเสี่ยง 1–5 แล้วส่งรายงานเข้า Line ทุกเช้า และแจ้งเตือนทันทีเมื่อเกิดเหตุวิกฤต — เพื่อให้ประชาชนทั่วไปรู้ความเสี่ยงในจังหวัดตัวเองโดยไม่ต้องหาข้อมูลเอง"

| 77 | 6 | 1–5 | 4 | 24/7 |
|----|---|-----|---|------|
| จังหวัดทั่วไทย | ประเภทภัย | Risk Score | Free APIs | Monitoring |

---

## Key Design Decisions

| หมวด | การตัดสินใจ | เหตุผล |
|------|------------|--------|
| 👥 ผู้ใช้ | ประชาชนทั่วไป | Key pivot จาก business — use case จริงกว่า |
| ⏱️ Frequency | Real-time ทุกชั่วโมง | ภัยธรรมชาติเปลี่ยนเร็ว ไม่รอ weekly |
| 🔢 Risk Scoring | Hybrid (code + LLM) | consistent + readable — code คำนวณ, Claude อธิบาย |
| 🔔 Notification | 2-tier alert | Daily 7AM + Emergency ทันทีเมื่อ score = 5 |
| 🗄️ Data | Free APIs ทั้งหมด | Open-Meteo · OpenAQ · USGS · NASA FIRMS |
| 💬 UX | Line Flex Message | คนไทยใช้ Line — card UI พร้อม score bar |

---

## Tech Stack

```
climate-risk-bot/
├── main.py                  # entry point + APScheduler
├── fetchers/
│   ├── weather.py           # Open-Meteo API → น้ำท่วม, พายุ, ภัยแล้ง
│   ├── air_quality.py       # OpenAQ API → PM2.5
│   ├── earthquake.py        # USGS API → แผ่นดินไหว
│   └── fire.py              # NASA FIRMS API → ไฟป่า
├── scorer/
│   └── risk_scorer.py       # threshold logic → score 1–5
├── llm/
│   └── analyzer.py          # Claude Haiku 4.5 → อธิบาย + context
├── bot/
│   └── line_bot.py          # Line Bot webhook + Flex Message
├── db/
│   └── database.py          # SQLite — users, risk_log, alerts_sent
└── .env                     # API keys (Anthropic, Line, NASA)
```

| Component | Technology |
|-----------|-----------|
| Language | Python |
| Scheduler | APScheduler |
| LLM | Claude Haiku 4.5 (Anthropic) |
| Notification | Line Bot SDK + Flex Message |
| Database | SQLite |
| Webhook | ngrok (local dev) |
| Config | python-dotenv |
