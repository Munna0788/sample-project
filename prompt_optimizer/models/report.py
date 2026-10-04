"""Final optimization report and objective schemas."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

from prompt_optimizer.models.candidate import PromptCandidate, TokenMetrics
from prompt_optimizer.models.evaluation import CandidateEvaluation


class OptimizationObjective(str, Enum):
    """Configurable goal for the optimizer."""
    MAXIMUM_QUALITY = "maximum_quality"           # Prioritize quality score above all, reject any degradation
    MAXIMUM_COMPRESSION = "maximum_compression"   # Maximize token reduction while satisfying guardrails
    BALANCED = "balanced"                         # Pareto-optimal balance of quality and token savings


class OptimizationIterationLog(BaseModel):
    """Log entry for an iterative refinement loop."""
    iteration: int = Field(description="Iteration number (1-based)")
    candidates_tested: int
    best_candidate_id: str
    best_quality_score: float
    notes: str


class FinalOptimizationReport(BaseModel):
    """Comprehensive, explainable optimization audit report."""
    original_prompt: str
    final_optimized_prompt: str
    
    # Token Metrics
    original_tokens: int
    final_tokens: int
    tokens_saved: int
    percentage_reduction: float
    
    # Quality Metrics
    original_quality_score: float
    final_quality_score: float
    quality_delta: float
    
    # Requirements & Invariant Integrity
    preserved_hard_requirements: List[str] = Field(
        default_factory=list,
        description="Critical constraints preserved with 100% fidelity"
    )
    preserved_soft_preferences: List[str] = Field(
        default_factory=list,
        description="Stylistic or soft preferences retained"
    )
    removed_redundancies: List[str] = Field(
        default_factory=list,
        description="List of repetitive instructions, fillers, or no-op phrases eliminated"
    )
    detected_ambiguities: List[str] = Field(
        default_factory=list,
        description="Ambiguities identified and clarified/resolved"
    )
    
    # Process & Trace
    optimization_iterations: int = Field(default=1)
    iteration_history: List[OptimizationIterationLog] = Field(default_factory=list)
    
    # Selection & Explainability
    selection_objective: OptimizationObjective
    selected_candidate_id: str
    selection_rationale: str = Field(
        description="Clear, explainable reason why this specific candidate was chosen over the others"
    )
    
    # All candidates for audit
    all_candidates: List[CandidateEvaluation] = Field(default_factory=list)
