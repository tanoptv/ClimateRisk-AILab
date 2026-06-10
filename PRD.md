# PRD — Climate Risk Line Bot

**Status:** Ready for implementation  
**Project:** AI Course Capstone — Advanced AI Engineering Day 3  
**Stack:** Python · Claude Haiku 4.5 · Line Bot · SQLite · APScheduler  

---

## Problem Statement

ประชาชนทั่วไปในประเทศไทยไม่มีวิธีง่ายๆ ในการติดตามความเสี่ยงภัยธรรมชาติที่กระทบพื้นที่ตัวเองโดยตรง หากต้องการทราบว่าจังหวัดที่อยู่อาศัยกำลังเผชิญกับน้ำท่วม ฝุ่น PM2.5 หรือไฟป่าหรือไม่ จำเป็นต้องเปิดเว็บไซต์หลายแหล่ง (กรมอุตุนิยมวิทยา, AirVisual, กรมอุทกศาสตร์) แล้วตีความข้อมูลดิบด้วยตนเอง โดยไม่มีระบบแจ้งเตือนเชิงรุกหรือการสรุปที่เข้าใจได้ทันที ปัญหานี้รุนแรงขึ้นเมื่อเกิดเหตุการณ์วิกฤตที่ต้องการการตอบสนองรวดเร็ว

---

## Solution

Line Bot ที่ดึงข้อมูลภัยธรรมชาติจาก 4 API ฟรีทุกชั่วโมง ให้ AI (Claude Haiku 4.5) วิเคราะห์และให้คะแนนความเสี่ยง 1–5 สำหรับ 6 ประเภทภัย ครอบคลุม 77 จังหวัดทั่วไทย จากนั้นส่งรายงานสรุปเข้า Line ทุกเช้า 07:00 น. และแจ้งเตือนฉุกเฉินทันทีเมื่อความเสี่ยงถึงระดับวิกฤต (score = 5) — เพื่อให้ประชาชนรู้ว่าควรระวังอะไรโดยไม่ต้องหาข้อมูลเอง

ผู้ใช้สมัครติดตามจังหวัดที่สนใจผ่านการพิมพ์คำสั่งใน Line chat โดยตรง ไม่ต้องดาวน์โหลดแอปเพิ่ม

---

## User Stories

### การสมัครและจัดการจังหวัด

1. As a ประชาชนทั่วไป, I want to พิมพ์ `/ติดตาม เชียงใหม่` ใน Line chat, so that ระบบจะเริ่มส่งรายงานความเสี่ยงของเชียงใหม่ให้ฉัน
2. As a ประชาชนทั่วไป, I want to ติดตามหลายจังหวัดพร้อมกันได้ เช่น `/ติดตาม เชียงใหม่ กรุงเทพมหานคร`, so that ฉันสามารถดูแลทั้งบ้านเกิดและที่อยู่ปัจจุบันได้พร้อมกัน
3. As a ประชาชนทั่วไป, I want to พิมพ์ `/จังหวัดของฉัน` เพื่อดูรายชื่อจังหวัดที่ติดตามอยู่, so that ฉันรู้ว่าระบบกำลัง monitor ที่ไหนบ้าง
4. As a ประชาชนทั่วไป, I want to พิมพ์ `/ช่วยเหลือ` เพื่อดูคำสั่งทั้งหมด, so that ฉันสามารถใช้งาน Bot ได้โดยไม่ต้องจำคำสั่งทั้งหมด
5. As a ประชาชนทั่วไป, I want to ได้รับข้อความยืนยันทันทีหลังสมัครติดตามจังหวัด, so that ฉันรู้ว่าคำสั่งทำงานสำเร็จ

### รายงานประจำวัน (Daily Summary)

6. As a ประชาชนทั่วไป, I want to ได้รับ Flex Message สรุปความเสี่ยงทุกเช้า 07:00 น., so that ฉันรู้ว่าวันนี้ควรระวังอะไรก่อนออกจากบ้าน
7. As a ประชาชนทั่วไป, I want to เห็น risk score 1–5 พร้อม progress bar สำหรับแต่ละประเภทภัยใน Flex Message, so that ฉันเข้าใจระดับความเสี่ยงได้ทันทีโดยไม่ต้องตีความตัวเลข
8. As a ประชาชนทั่วไป, I want to เห็นคำอธิบายภาษาไทยจาก AI ว่าทำไมถึงได้คะแนนนั้นและควรทำอะไร, so that ฉันรู้ว่าต้องปรับพฤติกรรมอย่างไร
9. As a ประชาชนทั่วไป, I want to เห็นสีที่แตกต่างกันตาม score (เขียว/เหลือง/ส้ม/แดง), so that ฉันอ่านระดับความเสี่ยงได้แวบเดียวโดยไม่ต้องอ่านตัวเลข
10. As a ประชาชนทั่วไป, I want to ได้รับรายงานแยกตามจังหวัด, so that ฉันไม่สับสนเมื่อติดตามหลายจังหวัดพร้อมกัน
11. As a ประชาชนทั่วไป, I want to เห็นรายงานครบทั้ง 6 ประเภทภัย (น้ำท่วม, PM2.5, ภัยแล้ง, พายุ, แผ่นดินไหว, ไฟป่า), so that ฉันมีภาพรวมความเสี่ยงครบถ้วน

### การแจ้งเตือนฉุกเฉิน (Emergency Alert)

12. As a ประชาชนทั่วไป, I want to ได้รับแจ้งเตือนทันทีเมื่อ risk score ถึง 5 (วิกฤต), so that ฉันมีเวลาตอบสนองก่อนสถานการณ์เลวร้ายลง
13. As a ประชาชนทั่วไป, I want to ให้ Emergency Alert ระบุจังหวัด ประเภทภัย และคำแนะนำชัดเจน, so that ฉันรู้ทันทีว่าต้องทำอะไรโดยไม่ต้องเปิดหาข้อมูลเพิ่ม
14. As a ประชาชนทั่วไป, I want to ไม่ได้รับ Emergency Alert ซ้ำสำหรับเหตุการณ์เดียวกันภายใน 6 ชั่วโมง, so that ฉันไม่ถูก spam notification จนเลิกใช้งาน
15. As a ประชาชนทั่วไป, I want to ยังคงได้รับ Daily Summary ปกติในตอนเช้า แม้จะมี Emergency Alert ในคืนก่อน, so that ฉันยังมีสรุปภาพรวมของวันนั้น

### ความครบถ้วนของข้อมูล

16. As a ประชาชนทั่วไป, I want to ระบบ check ความเสี่ยงทุกชั่วโมง, so that ข้อมูลที่ฉันได้รับสะท้อนสถานการณ์ปัจจุบัน ไม่ใช่ข้อมูลเก่า
17. As a ประชาชนทั่วไป, I want to ระบบรองรับทุกจังหวัดใน 77 จังหวัดของไทย, so that ฉันติดตามพื้นที่ที่สนใจได้ไม่ว่าจะอยู่ที่ไหน
18. As a ประชาชนทั่วไป, I want to ระบบยังส่งรายงานได้แม้ API ใดหนึ่งล่ม, so that ฉันยังได้ข้อมูลที่มีแม้ไม่ครบทุกประเภทภัย
19. As a ประชาชนทั่วไป, I want to เห็นคะแนนแต่ละประเภทภัยแยกกัน ไม่ใช่ค่าเฉลี่ยรวม, so that ฉันรู้ว่าภัยประเภทไหนที่น่าเป็นห่วงจริงๆ

### ความน่าเชื่อถือของ AI Explanation

20. As a ประชาชนทั่วไป, I want to AI อธิบายเป็นภาษาไทยที่อ่านง่าย ไม่ใช่ศัพท์เทคนิค, so that ฉันเข้าใจสถานการณ์ได้โดยไม่จำเป็นต้องมีความรู้ด้านวิทยาศาสตร์
21. As a ประชาชนทั่วไป, I want to AI ให้คำแนะนำที่ปฏิบัติได้จริง เช่น "ควรสวมหน้ากาก N95" หรือ "หลีกเลี่ยงพื้นที่ลุ่ม", so that ฉันรู้ว่าต้องทำอะไรต่อไป
22. As a ประชาชนทั่วไป, I want to คำอธิบายของ AI มีความยาวพอเหมาะ (2–3 ประโยค), so that ฉันอ่านบน Line ได้สะดวกโดยไม่ต้อง scroll มาก
23. As a ประชาชนทั่วไป, I want to เมื่อ score = 1 ระบบไม่เรียก LLM แต่แสดงข้อความ default, so that ไม่เสีย API cost โดยไม่จำเป็น

### Dashboard สำหรับทดสอบก่อนส่ง LINE จริง

24. As a ผู้พัฒนา, I want to เปิด dashboard บน localhost เพื่อดู users, จังหวัดที่ติดตาม, latest risk และ notification preview, so that ฉันทดสอบระบบได้โดยไม่ต้องส่งข้อความเข้า LINE จริง
25. As a ผู้พัฒนา, I want to trigger hourly check และ daily summary จาก dashboard ได้, so that ฉันทดสอบ flow หลักได้ทันทีโดยไม่ต้องรอ scheduler
26. As a ผู้พัฒนา, I want to ตั้งค่า `NOTIFICATION_MODE=dashboard` เพื่อบันทึก notification เป็น preview แทนการ push เข้า LINE, so that ฉัน demo และ debug ได้โดยไม่รบกวนผู้ใช้จริง
27. As a ผู้พัฒนา, I want to เห็นทั้ง plain text emergency alert และ Flex Message JSON preview ใน dashboard, so that ฉันตรวจรูปแบบข้อความก่อนเปิดใช้งาน LINE จริงได้

---

## Implementation Decisions

### Module Architecture

1. **ระบบแบ่งเป็น modules แยกกันชัดเจน** ตาม layer:
   - `fetchers/` — รับผิดชอบการดึงข้อมูลจาก external APIs เท่านั้น ไม่มี business logic
   - `scorer/` — pure functions คำนวณ risk score จาก threshold ไม่มี side effects
   - `llm/` — wrapper สำหรับ Anthropic API สร้าง explanation เป็นภาษาไทย
   - `bot/` — Flask webhook handler + Line SDK สำหรับ send/receive messages
   - `dashboard/` หรือ dashboard routes — local web UI สำหรับทดสอบและ preview notification โดยไม่ส่ง LINE จริง
   - `db/` — SQLite CRUD operations ทั้งหมดอยู่ที่นี่

2. **`main.py` เป็น orchestrator เท่านั้น** ไม่มี business logic ของตัวเอง — เพียงเรียก modules อื่น และจัดการ APScheduler

### Data Model (SQLite)

3. **3 tables:**
   - `users(user_id PK, provinces TEXT, created_at TEXT)` — provinces เก็บเป็น comma-separated string
   - `risk_log(id, province, hazard_type, score, raw_value, explanation, checked_at)` — บันทึกทุก check
   - `alerts_sent(id, user_id, province, hazard_type, score, sent_at)` — ใช้ตรวจสอบ duplicate alert

4. **provinces เก็บเป็น comma-separated string** ใน users table ไม่ใช่ many-to-many relation เพราะ scope ไม่จำเป็นต้องซับซ้อน

### Risk Scoring

5. **Hybrid scoring approach:** code คำนวณ score 1–5 จาก threshold แข็ง → ส่ง score + raw_value ให้ Claude อธิบาย context ไม่ให้ Claude ตัดสิน score เพื่อความ consistent

6. **Score thresholds แยกต่างหากสำหรับแต่ละ hazard type** ไม่มี global threshold — แต่ละ hazard function return `tuple[int, float]` (score, raw_value)

7. **Score = 1 ไม่เรียก LLM** — return hard-coded string "สถานการณ์ปกติ ไม่มีความเสี่ยงในขณะนี้" เพื่อลด API cost

### External APIs

8. **Data sources และ hazard mapping:**
   - Open-Meteo → น้ำท่วม (precipitation), พายุ (wind_speed), ภัยแล้ง (daily_precip_sum)
   - OpenAQ → PM2.5
   - USGS Earthquake API → magnitude + count ในรัศมี 300km
   - NASA FIRMS → fire count + FRP (Fire Radiative Power) ในรัศมี ~55km

9. **Fetcher failure isolation:** แต่ละ fetcher มี try/except ของตัวเอง return default zero-value dict เมื่อ error ระบบ check ต่อด้วยข้อมูลที่มี ไม่หยุดทำงานทั้งหมด

10. **Province data เก็บเป็น `data/provinces.json`** — `{"จังหวัด": {"lat": float, "lon": float}}` โหลดครั้งเดียวตอน startup

### Notification Logic

11. **2-tier notification:**
    - Daily Summary: APScheduler CronTrigger ทุกวัน 07:00 น. (Asia/Bangkok) ดึงข้อมูลล่าสุดจาก `risk_log`
    - Emergency Alert: ตรวจใน hourly_check loop — ถ้า score = 5 และยังไม่ได้ส่งใน 6 ชั่วโมงล่าสุด (ตรวจจาก `alerts_sent`) → ส่งทันที

12. **Daily Summary ใช้ `get_latest_risk()` ดึงจาก DB** ไม่ fetch APIs ใหม่ตอนส่ง — ข้อมูลมาจาก hourly check ล่าสุดแล้ว

13. **Emergency Alert เป็น plain TextMessage** ไม่ใช่ Flex Message — เพื่อให้ notification preview บน lock screen อ่านได้ทันที

14. **Daily Summary เป็น Flex Message** มี score bar สี และ explanation ของ Claude สำหรับแต่ละ hazard type

15. **Notification mode แยก dev/test ออกจาก LINE จริง** — `NOTIFICATION_MODE=dashboard` จะไม่เรียก LINE push API แต่เก็บ notification preview ให้ dashboard แสดงผล ส่วน `NOTIFICATION_MODE=line` จึงส่งเข้า LINE จริง

### Dashboard Test Mode

16. **Dashboard route หลักคือ `GET /dashboard`** แสดง users, จังหวัดที่ติดตาม, latest risk log และรายการ notification preview ล่าสุด

17. **Dashboard มี action สำหรับทดสอบ flow หลัก** ได้แก่ trigger hourly check, trigger daily summary และ clear preview notifications โดยไม่ต้องรอ APScheduler

18. **Dashboard preview ต้องแสดงทั้งข้อความและ payload** — Emergency Alert แสดง plain text preview, Daily Summary แสดง Flex payload JSON หรือ structured preview ที่ตรวจสอบได้

### LLM Integration

19. **Prompt เป็นภาษาไทย** — บอก role, จังหวัด, hazard_type, score, raw_value และขอ 3 ข้อ: เหตุผล/ผลกระทบ/คำแนะนำ ใน 2–3 ประโยค

20. **max_tokens = 200** สำหรับ explanation เพื่อควบคุม cost และความยาว message ที่เหมาะกับ Line

21. **Model: `claude-haiku-4-5-20251001`** — เร็ว ถูก เหมาะกับ structured output ที่ call ทุกชั่วโมง

### Deployment

22. **Local machine + ngrok** — `ngrok http 8000` สร้าง public HTTPS URL สำหรับ Line webhook — ngrok URL ต้องอัปเดตใน Line Developer Console ทุกครั้งที่รัน ngrok ใหม่

23. **Flask server และ APScheduler รันใน process เดียวกัน** ผ่าน `BackgroundScheduler` ไม่ใช่ `BlockingScheduler` เพื่อให้ Flask รันได้พร้อมกัน

24. **Environment variables ทั้งหมดใน `.env`** อ่านผ่าน `python-dotenv` — ไฟล์นี้ถูก gitignore

---

## Testing Decisions

### What makes a good test

Test พฤติกรรมที่มองเห็นจากภายนอก module — ไม่ test implementation details:
- ✅ Test ว่า `score_flood({"precipitation_max": 55})` คืน `(5, 55)`
- ❌ Test ว่า function ใช้ `if` หรือ `match` ภายใน
- ✅ Test ว่า fetcher ที่ได้รับ HTTP 500 คืน zero-value dict แทนที่จะ raise exception
- ❌ Test ว่า fetcher เรียก `requests.get` กี่ครั้ง

---

### Seam 1 — `scorer/risk_scorer.py` (สูงสุด, ง่ายสุด)

**ทำไมถึงเป็น seam ที่ดีที่สุด:** Pure functions ไม่มี I/O ไม่มี side effects ทดสอบได้ด้วย plain `assert` ไม่ต้อง mock อะไร

**สิ่งที่ test:**
- แต่ละ boundary ของ threshold: ค่าพอดีขอบ (เช่น precipitation = 50 → score 5, 49 → score 4)
- ค่า edge case: 0, negative (ถ้าเป็นไปได้), ค่าสูงมากๆ
- `score_all()` รวม output จาก fetchers ทั้งหมดได้ถูกต้อง
- return type เป็น `tuple[int, float]` เสมอ

**ตัวอย่าง test structure:**
```python
def test_flood_score_5_at_threshold():
    assert score_flood({"precipitation_max": 50}) == (5, 50)

def test_flood_score_4_just_below_threshold():
    assert score_flood({"precipitation_max": 49}) == (4, 49)

def test_flood_returns_raw_value():
    score, raw = score_flood({"precipitation_max": 25})
    assert raw == 25
```

---

### Seam 2 — `fetchers/*.py` (HTTP boundary)

**ทำไมถึงเป็น seam ที่ดี:** ทดสอบ normalisation logic ที่แปลง JSON response เป็น dict ที่ scorer ต้องการ โดยไม่ต้อง call API จริง

**สิ่งที่ test:**
- happy path: JSON response ถูกต้อง → dict ถูก shape
- error path: HTTP 500, timeout, empty response → คืน zero-value dict ไม่ raise
- edge case: ค่า `null` ใน JSON, empty array

**วิธี mock:** `unittest.mock.patch("requests.get")` หรือใช้ library `responses`

---

### Seam 3 — `llm/analyzer.py` (Anthropic API boundary)

**สิ่งที่ test:**
- score = 1 → คืน hard-coded string ไม่เรียก Anthropic client
- score ≥ 2 → เรียก `client.messages.create` พร้อม model ที่ถูกต้อง
- output เป็น string ไม่ว่า Anthropic จะคืน content รูปแบบใด
- prompt มีชื่อจังหวัดและ hazard type อยู่

**วิธี mock:** `unittest.mock.patch.object(anthropic.Anthropic, "messages")` หรือ inject mock client

---

### Seam 4 — `bot/line_bot.py` (Flask + Line SDK boundary)

**สิ่งที่ test:**
- POST `/callback` ที่มี signature ไม่ถูกต้อง → 400
- POST `/callback` พร้อม `/ติดตาม เชียงใหม่` event → เรียก `save_user_provinces` ถูก args
- POST `/callback` พร้อม `/จังหวัดของฉัน` event → reply message มีชื่อจังหวัด
- `send_flex_message` สร้าง Flex Message ที่มี score bar ครบทุก hazard

**วิธี test:** Flask test client + mock `MessagingApi` + mock `db` functions

---

### Modules ที่ไม่ test โดยตรง

- **`main.py`** — orchestration ล้วนๆ ทดสอบผ่าน integration tests ของ modules อื่นแทน
- **`db/database.py`** — ใช้ SQLite in-memory (`:memory:`) แทน file จริงใน test setup

---

*Note: ไม่มี issue tracker ที่ configure ไว้สำหรับ project นี้ — PRD นี้บันทึกเป็นไฟล์แทน*
