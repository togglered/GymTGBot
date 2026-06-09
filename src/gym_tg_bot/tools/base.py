from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ToolContext:
    chat_id: int


class Tool(ABC):
    @property
    @abstractmethod
    def definition(self) -> dict[str, object]: ...

    @abstractmethod
    async def __call__(self, arguments: dict[str, object], context: ToolContext) -> str: ...
