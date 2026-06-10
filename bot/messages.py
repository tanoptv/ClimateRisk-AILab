from typing import Any

from scorer.risk_scorer import HAZARD_LABELS, HAZARD_ORDER, SCORE_COLORS, SCORE_LABELS


def format_risk_rows(risks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_hazard = {row["hazard_type"] if "hazard_type" in row else row["hazard"]: row for row in risks}
    formatted = []
    for hazard in HAZARD_ORDER:
        row = by_hazard.get(hazard)
        if not row:
            continue
        score = int(row["score"])
        formatted.append(
            {
                "hazard": hazard,
                "label": HAZARD_LABELS.get(hazard, hazard),
                "score": score,
                "raw_value": float(row.get("raw_value", 0) or 0),
                "explanation": row.get("explanation", ""),
            }
        )
    return formatted


def build_emergency_text(province: str, hazard_label: str, score: int, explanation: str) -> str:
    return (
        "แจ้งเตือนฉุกเฉิน!\n\n"
        f"จังหวัด: {province}\n"
        f"{hazard_label} - ระดับ {score}/5 (วิกฤต)\n\n"
        f"{explanation}"
    )


def build_daily_flex_payload(province: str, risks: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for risk in format_risk_rows(risks):
        score = int(risk["score"])
        color = SCORE_COLORS[score]
        rows.append(
            {
                "type": "box",
                "layout": "vertical",
                "margin": "md",
                "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "text",
                                "text": risk["label"],
                                "size": "sm",
                                "weight": "bold",
                                "color": "#111827",
                                "flex": 3,
                            },
                            {
                                "type": "text",
                                "text": f"{score}/5 {SCORE_LABELS[score]}",
                                "size": "sm",
                                "color": color,
                                "align": "end",
                                "flex": 2,
                            },
                        ],
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "height": "7px",
                        "margin": "sm",
                        "backgroundColor": "#e5e7eb",
                        "cornerRadius": "4px",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "vertical",
                                "backgroundColor": color,
                                "cornerRadius": "4px",
                                "width": f"{score * 20}%",
                                "contents": [],
                            }
                        ],
                    },
                    {
                        "type": "text",
                        "text": risk["explanation"],
                        "size": "xs",
                        "color": "#4b5563",
                        "wrap": True,
                        "margin": "sm",
                    },
                ],
            }
        )

    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#ffffff",
            "paddingAll": "18px",
            "contents": [
                {
                    "type": "text",
                    "text": "รายงานความเสี่ยง",
                    "color": "#2563eb",
                    "size": "xs",
                    "weight": "bold",
                },
                {
                    "type": "text",
                    "text": province,
                    "color": "#111827",
                    "size": "xl",
                    "weight": "bold",
                    "margin": "sm",
                },
                {"type": "separator", "margin": "md", "color": "#e5e7eb"},
                *rows,
            ],
        },
    }


def build_daily_text_preview(province: str, risks: list[dict[str, Any]]) -> str:
    lines = [f"รายงานความเสี่ยง {province}"]
    for risk in format_risk_rows(risks):
        lines.append(f"- {risk['label']}: {risk['score']}/5 {SCORE_LABELS[int(risk['score'])]}")
    return "\n".join(lines)

