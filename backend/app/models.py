from enum import Enum
from pydantic import BaseModel, field_validator
from dataclasses import dataclass, field
from datetime import datetime


class EventType(str, Enum):
    MESSAGE = "message"
    SYSTEM = "system"


@dataclass
class BroadcastEvent:
    """Encapsulates the contract for all messages broadcast to SSE clients."""
    event_type: EventType
    text: str
    sender: str  # "user" or "telegram"
    timestamp: datetime = field(default_factory=datetime.now)


class SendMessageRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def text_not_blank(cls, v):
        if not v.strip():
            raise ValueError("text cannot be blank")
        return v.strip()


class SendMessageResponse(BaseModel):
    ok: bool
