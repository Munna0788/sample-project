"""Tests for in-memory prompt compilation cache."""

import pytest
import time
from prompt_optimizer.core.cache import PromptCache
from prompt_optimizer.backends.mock import MockLLMBackend
from prompt_optimizer.core.quick_optimizer import QuickOptimizer


def test_prompt_cache_set_and_get():
    cache = PromptCache(max_size=10, default_ttl_seconds=60)
    prompt = "Hello world"
    backend = "mock"
    data = {"result": "success"}

    assert cache.get(prompt, backend) is None
    cache.set(prompt, backend, data)
    assert cache.get(prompt, backend) == data


def test_prompt_cache_expiry():
    cache = PromptCache(max_size=10, default_ttl_seconds=1)
    prompt = "Fast expire prompt"
    cache.set(prompt, "mock", "cached_val", ttl=1)
    assert cache.get(prompt, "mock") == "cached_val"
    time.sleep(1.1)
    assert cache.get(prompt, "mock") is None


def test_quick_optimizer_hits_cache():
    backend = MockLLMBackend()
    cache = PromptCache()
    opt = QuickOptimizer(backend=backend, cache=cache)

    raw = "Extract numbers from input"
    # First call (miss)
    res1 = opt.optimize_quick(raw, force_generate=True)
    assert res1.status == "ready"

    # Second call (hit)
    res2 = opt.optimize_quick(raw, force_generate=False)
    assert res2.status == "ready"
    assert res2.concise.prompt_text == res1.concise.prompt_text
