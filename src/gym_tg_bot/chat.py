from typing import Literal, TypedDict

Role = Literal["user", "assistant"]


class ChatMessage(TypedDict):
    role: Role
    content: str
