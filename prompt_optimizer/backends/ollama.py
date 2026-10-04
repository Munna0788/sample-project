"""Ollama backend implementation for local LLM inference."""

import json
import logging
from typing import Optional, Dict, Any
import httpx

from prompt_optimizer.backends.base import BaseLLMBackend

logger = logging.getLogger(__name__)


class OllamaBackend(BaseLLMBackend):
    """Local inference backend powered by Ollama."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "goekdenizguelmez/JOSIEFIED-Qwen2.5:7b",
        timeout_seconds: float = 60.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def is_available(self) -> bool:
        """Verify Ollama is reachable and has models loaded."""
        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama availability check failed: {e}")
            return False

    def get_model_name(self) -> str:
        return f"ollama/{self.model}"

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> str:
        """Call Ollama /api/generate."""
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system_instruction:
            payload["system"] = system_instruction
        if json_mode:
            payload["format"] = "json"

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                res = client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )
                res.raise_for_status()
                data = res.json()
                return data.get("response", "").strip()
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise RuntimeError(f"Ollama backend failure: {e}") from e
