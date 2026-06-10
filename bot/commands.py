from dataclasses import dataclass


FOLLOW_COMMAND = "/ติดตาม"
MY_PROVINCES_COMMAND = "/จังหวัดของฉัน"
HELP_COMMAND = "/ช่วยเหลือ"


@dataclass(frozen=True)
class CommandResult:
    action: str
    provinces: list[str]
    reply_text: str | None = None


HELP_TEXT = (
    "คำสั่งที่ใช้ได้:\n"
    "/ติดตาม [จังหวัด] - เพิ่มจังหวัดที่ต้องการติดตาม\n"
    "/จังหวัดของฉัน - ดูจังหวัดที่ติดตามอยู่\n"
    "/ช่วยเหลือ - ดูคำสั่งทั้งหมด"
)


def parse_command(text: str) -> CommandResult:
    clean = text.strip()
    if clean.startswith(FOLLOW_COMMAND):
        raw = clean.removeprefix(FOLLOW_COMMAND).strip()
        provinces = [part.strip() for part in raw.split() if part.strip()]
        return CommandResult(action="follow", provinces=provinces)
    if clean == MY_PROVINCES_COMMAND:
        return CommandResult(action="my_provinces", provinces=[])
    if clean == HELP_COMMAND:
        return CommandResult(action="help", provinces=[], reply_text=HELP_TEXT)
    return CommandResult(action="unknown", provinces=[], reply_text="พิมพ์ /ช่วยเหลือ เพื่อดูคำสั่งทั้งหมด")


def validate_provinces(provinces: list[str], province_map: dict[str, dict[str, float]]) -> tuple[list[str], list[str]]:
    valid = []
    invalid = []
    seen = set()
    for province in provinces:
        if province in province_map and province not in seen:
            valid.append(province)
            seen.add(province)
        elif province not in province_map:
            invalid.append(province)
    return valid, invalid


def build_command_reply(
    user_id: str,
    text: str,
    province_map: dict[str, dict[str, float]],
    get_user_provinces,
    save_user_provinces,
) -> str:
    command = parse_command(text)
    if command.action == "follow":
        if not command.provinces:
            return "กรุณาระบุชื่อจังหวัด เช่น /ติดตาม เชียงใหม่ กรุงเทพมหานคร"
        valid, invalid = validate_provinces(command.provinces, province_map)
        if invalid:
            return f"ไม่พบจังหวัด: {', '.join(invalid)}\nกรุณาตรวจสอบชื่อจังหวัดแล้วลองใหม่"
        save_user_provinces(user_id, valid)
        return f"ติดตามแล้ว: {', '.join(valid)}\nจะได้รับรายงานทุกเช้า 07:00 น."

    if command.action == "my_provinces":
        provinces = get_user_provinces(user_id)
        if not provinces:
            return "ยังไม่ได้ติดตามจังหวัดใด"
        return f"จังหวัดที่ติดตาม: {', '.join(provinces)}"

    return command.reply_text or HELP_TEXT

