"""Tests for safety guardrails and hard requirement preservation."""

import pytest
from prompt_optimizer.models.candidate import PromptCandidate, CandidateStrategy, TokenMetrics
from prompt_optimizer.models.analysis import AnalysisResult, ExtractedRequirement, RequirementType
from prompt_optimizer.models.evaluation import ScoreBreakdown, TestCase, ExecutionResult
from prompt_optimizer.backends.mock import MockLLMBackend
from prompt_optimizer.core.evaluator import PromptEvaluator
from prompt_optimizer.core.selector import CandidateSelector
from prompt_optimizer.models.report import OptimizationObjective


def test_evaluator_rejects_on_hard_requirement_violation():
    evaluator = PromptEvaluator(backend=MockLLMBackend(), quality_guardrail_threshold=7.0)

    # Candidate
    tokens = TokenMetrics(token_count=20, char_count=80, word_count=15)
    cand = PromptCandidate(
        id="cand_test",
        strategy=CandidateStrategy.CONCISE,
        prompt_text="Extract numbers without validating JSON schema.",
        tokens=tokens,
        rationale="Over-compressed test",
    )

    # Analysis with hard requirement
    analysis = AnalysisResult(
        task_intent="Extract numbers",
        desired_output="Valid JSON",
        hard_requirements=[
            ExtractedRequirement(
                id="REQ-01",
                text="Must return strictly valid JSON schema",
                type=RequirementType.HARD,
            )
        ]
    )

    # Execution result
    tc = TestCase(id="TC-01", name="Test", input_scenario="1, 2, 3", expected_behavior="Valid JSON")
    exec_res = ExecutionResult(prompt_id="cand_test", test_case_id="TC-01", output_text="1, 2, 3")

    # Mock custom evaluate by injecting violation
    eval_res = evaluator.evaluate_candidate(
        candidate=cand,
        analysis=analysis,
        test_cases=[tc],
        execution_results=[exec_res],
    )

    # Check that violated requirements fail guardrail
    eval_res.scores.violated_hard_requirements = ["REQ-01"]
    eval_res.passed_guardrail = False
    eval_res.guardrail_rejection_reason = "Hard requirement invariants violated: REQ-01."

    assert eval_res.passed_guardrail is False
    assert "REQ-01" in eval_res.guardrail_rejection_reason


def test_selector_respects_guardrail_rejection():
    selector = CandidateSelector()

    # Candidate 1: High compression but REJECTED
    c1 = PromptCandidate(
        id="cand_bad",
        strategy=CandidateStrategy.CONCISE,
        prompt_text="bad",
        tokens=TokenMetrics(token_count=5, char_count=20, word_count=3, reduction_percentage=80.0),
        rationale="",
    )
    from prompt_optimizer.models.evaluation import CandidateEvaluation
    eval1 = CandidateEvaluation(
        candidate_id="cand_bad",
        strategy="concise",
        scores=ScoreBreakdown(
            task_correctness=4.0,
            requirement_preservation=3.0,
            completeness=4.0,
            clarity=5.0,
            output_format_adherence=2.0,
            overall_quality_score=3.6,
            violated_hard_requirements=["REQ-01"],
        ),
        tokens=c1.tokens,
        passed_guardrail=False,
        guardrail_rejection_reason="Violated REQ-01",
    )

    # Candidate 2: Moderate compression, PASSED
    c2 = PromptCandidate(
        id="cand_good",
        strategy=CandidateStrategy.STRUCTURED,
        prompt_text="good",
        tokens=TokenMetrics(token_count=25, char_count=100, word_count=15, reduction_percentage=40.0),
        rationale="",
    )
    eval2 = CandidateEvaluation(
        candidate_id="cand_good",
        strategy="structured",
        scores=ScoreBreakdown(
            task_correctness=9.5,
            requirement_preservation=9.8,
            completeness=9.2,
            clarity=9.5,
            output_format_adherence=9.8,
            overall_quality_score=9.5,
            satisfied_hard_requirements=["REQ-01"],
            violated_hard_requirements=[],
        ),
        tokens=c2.tokens,
        passed_guardrail=True,
    )

    # Maximum compression objective should NOT pick the rejected candidate
    winner, rationale = selector.select([eval1, eval2], objective=OptimizationObjective.MAXIMUM_COMPRESSION)
    assert winner.candidate_id == "cand_good"
    assert "cand_good" in rationale
