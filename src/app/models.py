"""Small platform-neutral message types."""
from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(frozen=True)
class IncomingMessage:
    platform: str
    conversation_id: str
    conversation_type: Literal["group", "direct"]
    user_id: str
    message_id: str
    text: str
    timestamp: datetime
    nickname: str = ""

    @property
    def session_id(self) -> str:
        return f"{self.platform}:{self.conversation_type}:{self.conversation_id}:{self.user_id}"
