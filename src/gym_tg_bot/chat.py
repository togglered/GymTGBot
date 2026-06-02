from dataclasses import dataclass
from typing import Literal

Role = Literal["user", "assistant"]


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, object]


@dataclass(frozen=True)
class ToolResult:
    tool_call_id: str
    content: str


@dataclass(frozen=True)
class TextPart:
    text: str
    type: Literal["text"] = "text"


@dataclass(frozen=True)
class ImagePart:
    image_url: str  # data:image/jpeg;base64,...
    type: Literal["image_url"] = "image_url"


ContentPart = TextPart | ImagePart


@dataclass(frozen=True)
class ChatMessage:
    role: Role
    content: str | list[ContentPart]
