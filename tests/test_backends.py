"""Tests for pluggable LLM backends."""

import pytest
from prompt_optimizer.backends.mock import MockLLMBackend
from prompt_optimizer.backends.ollama import OllamaBackend
from prompt_optimizer.backends.openai_compat import OpenAICompatibleBackend


def test_mock_backend_availability():
    mock = MockLLMBackend()
    assert mock.is_available() is True
    assert mock.get_model_name() == "mock/mock-agentic-v1"


def test_mock_backend_generate_stages():
    mock = MockLLMBackend()
    # Test analysis stage prompt
    analysis_resp = mock.generate("analyze the following prompt: do something", json_mode=True)
    assert "task_intent" in analysis_resp
    assert "hard_requirements" in analysis_resp

    # Test candidate generation stage prompt
    cand_resp = mock.generate("generate candidate prompts", json_mode=True)
    assert "candidates" in cand_resp
    assert "cand_concise" in cand_resp


def test_openai_backend_unconfigured():
    backend = OpenAICompatibleBackend(api_key="")
    assert backend.is_available() is False
    with pytest.raises(ValueError):
        backend.generate("test")
