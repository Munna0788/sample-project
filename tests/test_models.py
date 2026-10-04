"""Tests for Pydantic schema models."""

import pytest
from prompt_optimizer.models import (
    RequirementType,
    ExtractedRequirement,
    AnalysisResult,
    OptimizationPlan,
    CandidateStrategy,
    TokenMetrics,
    PromptCandidate,
    TestCase,
    ScoreBreakdown,
    CandidateEvaluation,
    OptimizationObjective,
    FinalOptimizationReport,
)


def test_extracted_requirement_hard_and_soft():
    hard_req = ExtractedRequirement(
        id="REQ-01",
        text="Output format must be valid JSON",
        type=RequirementType.HARD,
        category="format",
    )
    assert hard_req.type == RequirementType.HARD

    soft_req = ExtractedRequirement(
        id="PREF-01",
        text="Use polite tone if possible",
        type=RequirementType.SOFT,
        category="style",
    )
    assert soft_req.type == RequirementType.SOFT


def test_final_report_serialization():
    tokens = TokenMetrics(
        token_count=50,
        char_count=200,
        word_count=35,
        token_delta=25,
        reduction_percentage=33.33,
    )
    report = FinalOptimizationReport(
        original_prompt="Original verbose prompt here...",
        final_optimized_prompt="Optimized prompt here...",
        original_tokens=75,
        final_tokens=50,
        tokens_saved=25,
        percentage_reduction=33.33,
        original_quality_score=8.5,
        final_quality_score=9.4,
        quality_delta=0.9,
        preserved_hard_requirements=["REQ-01: Valid JSON"],
        preserved_soft_preferences=[],
        removed_redundancies=["Please please"],
        detected_ambiguities=[],
        optimization_iterations=1,
        selection_objective=OptimizationObjective.BALANCED,
        selected_candidate_id="cand_structured",
        selection_rationale="Achieved Pareto optimal balance.",
    )

    data = report.model_dump()
    assert data["tokens_saved"] == 25
    assert data["selection_objective"] == "balanced"
