"""Tests for QuickOptimizer dual-result execution and ambiguity detection."""

import pytest
from prompt_optimizer.backends.mock import MockLLMBackend
from prompt_optimizer.core.quick_optimizer import QuickOptimizer
from prompt_optimizer.models.quick import QuickOptimizeResponse


def test_quick_optimizer_returns_clarification_on_ambiguity():
    backend = MockLLMBackend()
    quick_opt = QuickOptimizer(backend=backend)

    raw_prompt = "Hey please make me something short and cool."
    resp: QuickOptimizeResponse = quick_opt.optimize_quick(raw_prompt)

    # Mock analyzer returns ambiguities by default
    assert resp.status == "needs_clarification"
    assert len(resp.clarification_questions) > 0
    assert resp.concise is None
    assert resp.high_precision is None


def test_quick_optimizer_returns_dual_results_when_clarified():
    backend = MockLLMBackend()
    quick_opt = QuickOptimizer(backend=backend)

    raw_prompt = "Hey please extract all the metrics and output valid JSON."
    clarification_answers = {"CLAR-01": "Max output 100 words"}

    resp: QuickOptimizeResponse = quick_opt.optimize_quick(
        raw_prompt=raw_prompt,
        clarification_answers=clarification_answers,
    )

    assert resp.status == "ready"
    assert resp.concise is not None
    assert resp.high_precision is not None

    # Verify Result 1: Concise
    assert resp.concise.title == "Concise (Fast & Lean)"
    assert resp.concise.token_count > 0
    assert len(resp.concise.prompt_text) > 0

    # Verify Result 2: High Precision
    assert resp.high_precision.title == "High Precision (Strict & Complete)"
    assert resp.high_precision.token_count > 0
    assert len(resp.high_precision.prompt_text) > 0
    assert "# Role" not in resp.high_precision.prompt_text


def test_quick_optimizer_force_generate():
    backend = MockLLMBackend()
    quick_opt = QuickOptimizer(backend=backend)

    raw_prompt = "Process the data immediately."
    resp: QuickOptimizeResponse = quick_opt.optimize_quick(raw_prompt, force_generate=True)

    assert resp.status == "ready"
    assert resp.concise is not None
    assert resp.high_precision is not None


def test_quick_optimizer_outputs_are_dynamic_for_different_inputs():
    backend = MockLLMBackend()
    quick_opt = QuickOptimizer(backend=backend)

    p1 = "Write a Python script to monitor CPU usage and alert if above 80%"
    p2 = "Draft a polite customer support email apologizing for a delayed package"

    res1 = quick_opt.optimize_quick(p1, force_generate=True)
    res2 = quick_opt.optimize_quick(p2, force_generate=True)

    # Ensure high precision prompt is distinct and tailored to each input
    assert res1.high_precision.prompt_text != res2.high_precision.prompt_text
    assert "Python" in res1.high_precision.prompt_text
    assert "Customer" in res2.high_precision.prompt_text or "Support" in res2.high_precision.prompt_text
    assert "CPU" in res1.high_precision.prompt_text or "monitor" in res1.high_precision.prompt_text

