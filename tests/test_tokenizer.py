"""Tests for deterministic token measurement engine."""

import pytest
from prompt_optimizer.core.tokenizer import TokenizerEngine


def test_tokenizer_counts_tokens():
    engine = TokenizerEngine()
    text = "Hello world! This is a prompt optimization test."
    tokens = engine.count_tokens(text)
    assert tokens > 0
    assert isinstance(tokens, int)


def test_tokenizer_measure_metrics():
    engine = TokenizerEngine()
    original_text = "Please write a python script that will definitely parse a json file and output facts."
    orig_metrics = engine.measure(original_text)
    assert orig_metrics.token_count > 0
    assert orig_metrics.word_count == 15
    assert orig_metrics.token_delta == 0
    assert orig_metrics.reduction_percentage == 0.0

    # Shorter candidate
    cand_text = "Write Python script to parse JSON and output facts."
    cand_metrics = engine.measure(cand_text, original_tokens=orig_metrics.token_count)
    assert cand_metrics.token_count < orig_metrics.token_count
    assert cand_metrics.token_delta > 0
    assert cand_metrics.reduction_percentage > 0.0


def test_tokenizer_empty_string():
    engine = TokenizerEngine()
    metrics = engine.measure("")
    assert metrics.token_count == 0
    assert metrics.word_count == 0
    assert metrics.char_count == 0
