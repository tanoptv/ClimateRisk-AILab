from llm.analyzer import NORMAL_EXPLANATION, analyze_risk, build_prompt


class FakeMessages:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return type("Message", (), {"content": [type("Block", (), {"text": "คำอธิบายทดสอบ"})()]})()


class FakeClient:
    def __init__(self):
        self.messages = FakeMessages()


def test_score_one_does_not_call_client():
    client = FakeClient()
    assert analyze_risk("เชียงใหม่", "flood", 1, 0, client=client) == NORMAL_EXPLANATION
    assert client.messages.calls == []


def test_score_two_calls_client_with_prompt():
    client = FakeClient()
    assert analyze_risk("เชียงใหม่", "pm25", 2, 55, client=client) == "คำอธิบายทดสอบ"
    call = client.messages.calls[0]
    assert call["model"] == "claude-haiku-4-5-20251001"
    assert "เชียงใหม่" in call["messages"][0]["content"]
    assert "ฝุ่น PM2.5" in build_prompt("เชียงใหม่", "pm25", 2, 55)

