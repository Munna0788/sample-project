"""End-to-end test suite for the PromptOptimizerAgent pipeline."""

import pytest
from prompt_optimizer.backends.mock import MockLLMBackend
from prompt_optimizer.core.optimizer import PromptOptimizerAgent
from prompt_optimizer.models.report import OptimizationObjective


def test_full_optimization_pipeline_balanced():
    backend = MockLLMBackend()
    agent = PromptOptimizerAgent(backend=backend)

    raw_prompt = (
        "Hey! Please could you kindly act as a senior python developer and please write me a python function "
        "that reads a csv file and calculates the averages. Please make sure it's valid json and please never make "
        "up data and please make sure to be very fast and handle errors. As I said before, please make sure it's valid JSON!"
    )

    report = agent.optimize(
        raw_prompt=raw_prompt,
        objective=OptimizationObjective.BALANCED,
    )

    assert report is not None
    assert report.original_tokens > 0
    assert report.final_tokens > 0
    assert len(report.all_candidates) >= 3
    assert len(report.preserved_hard_requirements) > 0
    assert report.selection_objective == OptimizationObjective.BALANCED
    assert report.selected_candidate_id in ["cand_concise", "cand_structured", "cand_operational"]
    assert report.final_quality_score >= 7.0


def test_optimization_pipeline_maximum_compression():
    backend = MockLLMBackend()
    agent = PromptOptimizerAgent(backend=backend)

    raw_prompt = (
        "Hello please could you kindly do this task for me with great care and attention? "
        "I really need you to make sure that you do not forget anything that I am telling you right now. "
        "Please extract all the metrics and errors from the input data that I am giving you, "
        "and make sure it is valid JSON with summary and errors keys. Please do not hallucinate any missing data "
        "and please keep it under 150 words as I mentioned earlier. Thank you so much!"
    )
    report = agent.optimize(
        raw_prompt=raw_prompt,
        objective=OptimizationObjective.MAXIMUM_COMPRESSION,
    )

    assert report.selection_objective == OptimizationObjective.MAXIMUM_COMPRESSION
    assert report.percentage_reduction > 0.0
    assert report.tokens_saved > 0


def test_optimization_pipeline_with_clarifications():
    backend = MockLLMBackend()
    agent = PromptOptimizerAgent(backend=backend)

    raw_prompt = "Build a summary tool."
    clarifications = {"CLAR-01": "Target output maximum 100 words"}

    report = agent.optimize(
        raw_prompt=raw_prompt,
        objective=OptimizationObjective.MAXIMUM_QUALITY,
        clarification_answers=clarifications,
    )

    assert report.selected_candidate_id is not None
