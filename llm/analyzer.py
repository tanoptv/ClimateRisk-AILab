import os
from typing import Any


NORMAL_EXPLANATION = "สถานการณ์ปกติ ไม่มีความเสี่ยงในขณะนี้"
MODEL = "claude-haiku-4-5-20251001"

HAZARD_TH = {
    "flood": "น้ำท่วม",
    "pm25": "ฝุ่น PM2.5",
    "drought": "ภัยแล้ง",
    "storm": "พายุ",
    "earthquake": "แผ่นดินไหว",
    "fire": "ไฟป่า",
}


def build_prompt(province: str, hazard_type: str, score: int, raw_value: float) -> str:
    hazard_th = HAZARD_TH.get(hazard_type, hazard_type)
    return f"""คุณคือผู้เชี่ยวชาญด้านภัยธรรมชาติของประเทศไทย
ให้ข้อมูลสั้นกระชับ 2-3 ประโยค เป็นภาษาไทยที่ประชาชนทั่วไปอ่านเข้าใจง่าย

จังหวัด: {province}
ประเภทภัย: {hazard_th}
ระดับความเสี่ยง: {score}/5
ค่าที่วัดได้: {raw_value:.1f}

อธิบายให้ครอบคลุม 1) ทำไมถึงได้คะแนนนี้ 2) ผลกระทบที่อาจเกิดขึ้น 3) ประชาชนควรทำอะไร
ห้ามขึ้นต้นด้วย "จากข้อมูล" หรือ "ตามที่"
"""


def _extract_text(message: Any) -> str:
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list) and content:
        first = content[0]
        return getattr(first, "text", str(first)).strip()
    return str(content).strip()


def analyze_risk(
    province: str,
    hazard_type: str,
    score: int,
    raw_value: float,
    client: Any | None = None,
) -> str:
    if score <= 1:
        return NORMAL_EXPLANATION

    prompt = build_prompt(province, hazard_type, score, raw_value)
    try:
        if client is None:
            import anthropic

            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
        message = client.messages.create(
            model=MODEL,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        text = _extract_text(message)
        return text or "ระบบไม่สามารถสร้างคำอธิบายได้ในขณะนี้ กรุณาติดตามสถานการณ์จากหน่วยงานทางการ"
    except Exception as exc:
        print(f"LLM analyzer error: {exc}")
        return "ระบบไม่สามารถสร้างคำอธิบายได้ในขณะนี้ กรุณาติดตามสถานการณ์จากหน่วยงานทางการ"

