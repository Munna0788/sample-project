"""Tests for benchmark suite."""

import pytest
from prompt_optimizer.backends.mock import MockLLMBackend
from prompt_optimizer.core.optimizer import PromptOptimizerAgent
from prompt_optimizer.benchmarks.suite import BenchmarkSuite


def test_benchmark_suite_runs_all():
    backend = MockLLMBackend()
    agent = PromptOptimizerAgent(backend=backend)
    suite = BenchmarkSuite(agent=agent)

    report = suite.run_all()
    assert report.total_benchmarks == 3
    assert len(report.results) == 3
    assert report.invariant_preservation_rate == 100.0
    for res in report.results:
        assert res.original_tokens > 0
        assert res.final_tokens > 0
        assert res.quality_score > 0
