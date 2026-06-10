import os
from typing import Any

from flask import Blueprint, abort, request

from bot.commands import build_command_reply
from db.database import get_user_provinces, load_provinces, save_user_provinces


line_blueprint = Blueprint("line_bot", __name__)
PROVINCES = None
LINE_STATE = None


def _load_province_map() -> dict[str, dict[str, float]]:
    global PROVINCES
    if PROVINCES is None:
        PROVINCES = load_provinces()
    return PROVINCES


def _line_clients() -> tuple[Any, Any, Any, Any, Any]:
    global LINE_STATE
    if LINE_STATE is not None:
        return LINE_STATE

    from linebot.v3 import WebhookHandler
    from linebot.v3.messaging import ApiClient, Configuration, MessagingApi
    from linebot.v3.webhooks import MessageEvent, TextMessageContent

    configuration = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN", ""))
    handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET", ""))
    LINE_STATE = (configuration, handler, ApiClient, MessagingApi, (MessageEvent, TextMessageContent))
    return LINE_STATE


@line_blueprint.route("/callback", methods=["POST"])
def callback():
    try:
        from linebot.v3.exceptions import InvalidSignatureError
    except Exception:
        abort(503)

    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    _, handler, _, _, _ = _line_clients()
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


def register_line_handlers() -> None:
    try:
        from linebot.v3.messaging import ReplyMessageRequest, TextMessage
        from linebot.v3.webhooks import MessageEvent, TextMessageContent
    except Exception:
        return

    configuration, handler, ApiClient, MessagingApi, _ = _line_clients()

    @handler.add(MessageEvent, message=TextMessageContent)
    def handle_message(event):
        user_id = event.source.user_id
        reply_text = build_command_reply(
            user_id,
            event.message.text,
            _load_province_map(),
            get_user_provinces,
            save_user_provinces,
        )
        with ApiClient(configuration) as api_client:
            MessagingApi(api_client).reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)],
                )
            )


def push_text_message(user_id: str, text: str) -> None:
    from linebot.v3.messaging import ApiClient, Configuration, MessagingApi, PushMessageRequest, TextMessage

    configuration = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN", ""))
    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).push_message(
            PushMessageRequest(to=user_id, messages=[TextMessage(text=text)])
        )


def push_flex_message(user_id: str, alt_text: str, payload: dict[str, Any]) -> None:
    from linebot.v3.messaging import (
        ApiClient,
        Configuration,
        FlexContainer,
        FlexMessage,
        MessagingApi,
        PushMessageRequest,
    )

    configuration = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN", ""))
    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).push_message(
            PushMessageRequest(
                to=user_id,
                messages=[FlexMessage(alt_text=alt_text, contents=FlexContainer.from_dict(payload))],
            )
        )
