from abc import ABC, abstractmethod

from app.ai.context import AIContext


class AIProvider(ABC):
    @abstractmethod
    def analyze(self, context: AIContext, prompt: str) -> str:
        raise NotImplementedError
