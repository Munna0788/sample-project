"""Base abstraction for replaceable LLM backends."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class BaseLLMBackend(ABC):
    """Abstract interface for LLM execution backends (Ollama, OpenAI, Gemini, Claude, Mock)."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> str:
        """Execute a completion query against the LLM backend."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the backend is reachable and responsive."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the current model identifier."""
        pass
