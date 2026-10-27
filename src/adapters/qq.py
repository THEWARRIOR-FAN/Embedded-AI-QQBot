"""QQ botpy adapter. Translates SDK callbacks to application messages."""
import re
from datetime import datetime

from app.models import IncomingMessage

_AT_TAG = re.compile(r'<@!\d+>|<@\d+>|<at\s+[^/]*?/>')


def strip_at(text: str) -> str:
    return _AT_TAG.sub("", text).strip()


def group_message(message) -> IncomingMessage:
    user_id = str(getattr(message.author, "id", "") or message.group_openid)
    text = strip_at(message.content or "") or "（对方只@了我，没说话）"
    return IncomingMessage("qq", str(message.group_openid), "group", user_id,
                           str(message.id), text, datetime.now(),
                           getattr(message.author, "username", "") or "")


def direct_message(message) -> IncomingMessage:
    user_id = str(getattr(message.author, "user_openid", "") or getattr(message.author, "id", ""))
    text = strip_at(message.content or "") or "（对方发了个空消息）"
    return IncomingMessage("qq", user_id, "direct", user_id, str(message.id), text,
                           datetime.now(), getattr(message.author, "username", "") or "")
