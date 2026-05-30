from abc import ABC, abstractmethod


class Tool(ABC):
    @property
    @abstractmethod
    def definition(self) -> dict[str, object]: ...

    @abstractmethod
    async def __call__(self, **kwargs: object) -> str: ...
