"""Deterministic token measurement engine."""

import re
import logging
from typing import Optional
import tiktoken

from prompt_optimizer.models.candidate import TokenMetrics

logger = logging.getLogger(__name__)


class TokenizerEngine:
    """Calculates deterministic token and linguistic metrics using pure Python."""

    def __init__(self, encoding_name: str = "cl100k_base"):
        self.encoding_name = encoding_name
        try:
            self._encoder = tiktoken.get_encoding(encoding_name)
        except Exception as e:
            logger.warning(f"Could not load tiktoken encoding '{encoding_name}': {e}. Using fallback.")
            self._encoder = None

    def count_tokens(self, text: str) -> int:
        """Count exact tokens deterministically."""
        if not text:
            return 0
        if self._encoder is not None:
            return len(self._encoder.encode(text))
        # Deterministic regex approximation if tiktoken encoding unavailable
        tokens = re.findall(r"\w+|[^\w\s]", text, re.UNICODE)
        return len(tokens)

    def measure(self, text: str, original_tokens: Optional[int] = None) -> TokenMetrics:
        """Measure full token metrics, character count, and comparative reduction."""
        text = text.strip() if text else ""
        token_count = self.count_tokens(text)
        char_count = len(text)
        word_count = len(text.split()) if text else 0

        token_delta = 0
        reduction_pct = 0.0

        if original_tokens is not None and original_tokens > 0:
            token_delta = original_tokens - token_count
            reduction_pct = round((token_delta / original_tokens) * 100.0, 2)

        return TokenMetrics(
            token_count=token_count,
            char_count=char_count,
            word_count=word_count,
            token_delta=token_delta,
            reduction_percentage=reduction_pct,
        )
