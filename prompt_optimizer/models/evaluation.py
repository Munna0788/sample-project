"""Evaluation criteria, test case execution, and scoring schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field
from prompt_optimizer.models.candidate import TokenMetrics


class TestCase(BaseModel):
    """Synthetic or extracted test scenario to evaluate prompt execution."""
    __test__ = False
    id: str = Field(description="e.g. TC-01")
    name: str = Field(description="Descriptive title of test case")
    input_scenario: str = Field(description="Simulated user input or runtime scenario")
    expected_behavior: str = Field(description="What the LLM must adhere to according to original requirements")


class ExecutionResult(BaseModel):
    """Output from executing a prompt against a test case."""
    prompt_id: str = Field(description="original or candidate_id")
    test_case_id: str = Field(description="TC-01, etc.")
    output_text: str = Field(description="Actual LLM response")
    latency_ms: float = Field(default=0.0, description="Execution time in milliseconds")
    error: Optional[str] = Field(default=None)


class ScoreBreakdown(BaseModel):
    """Multi-dimensional evaluation scores on a 0.0 - 10.0 scale."""
    task_correctness: float = Field(ge=0.0, le=10.0, description="Does output accomplish the primary intent?")
    requirement_preservation: float = Field(ge=0.0, le=10.0, description="Are all hard & soft requirements satisfied?")
    completeness: float = Field(ge=0.0, le=10.0, description="Is the output comprehensive without missing facets?")
    clarity: float = Field(ge=0.0, le=10.0, description="Is the output articulate, clean, and unambiguous?")
    output_format_adherence: float = Field(ge=0.0, le=10.0, description="Did output strictly follow requested schema/format?")
    
    overall_quality_score: float = Field(ge=0.0, le=10.0, description="Weighted composite quality score")
    
    satisfied_hard_requirements: List[str] = Field(default_factory=list)
    violated_hard_requirements: List[str] = Field(default_factory=list)
    evaluation_notes: str = Field(default="", description="Detailed qualitative feedback and diagnostics")


class CandidateEvaluation(BaseModel):
    """Complete evaluation report for an individual candidate."""
    candidate_id: str
    strategy: str
    scores: ScoreBreakdown
    tokens: TokenMetrics
    
    passed_guardrail: bool = Field(
        description="True if quality performance meets or exceeds safety threshold and no hard requirements violated"
    )
    guardrail_rejection_reason: Optional[str] = Field(
        default=None,
        description="Explanation if this candidate was rejected by safety invariants"
    )
    
    composite_score: float = Field(
        default=0.0,
        description="Rank score calculated based on the chosen optimization objective"
    )
    test_executions: List[ExecutionResult] = Field(default_factory=list)
