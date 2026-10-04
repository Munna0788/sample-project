"""Optimization Plan schemas."""

from typing import List
from pydantic import BaseModel, Field


class PlanAction(BaseModel):
    """Specific edit or transformation action."""
    action_type: str = Field(description="COMPRESS, REMOVE, MERGE, REORGANIZE, CLARIFY")
    target: str = Field(description="Original phrase or pattern targeted")
    replacement: str = Field(description="Optimized replacement or structured equivalent")
    rationale: str = Field(description="Reason for this transformation")


class OptimizationPlan(BaseModel):
    """Declarative plan describing planned transformations before candidate generation."""
    compression_targets: List[str] = Field(
        default_factory=list,
        description="Verbose clauses to compress into concise directives"
    )
    removal_targets: List[str] = Field(
        default_factory=list,
        description="Filler words, conversational preambles, and duplicate instructions to delete"
    )
    merge_targets: List[str] = Field(
        default_factory=list,
        description="Scattered related constraints to consolidate into single coherent rules"
    )
    reorganization_strategy: str = Field(
        description="Structural hierarchy (e.g., Role -> Context -> Task -> Constraints -> Output Format)"
    )
    hard_requirement_invariants: List[str] = Field(
        default_factory=list,
        description="Hard requirements that MUST remain intact across all candidates"
    )
    planned_actions: List[PlanAction] = Field(
        default_factory=list,
        description="Granular actions taken during optimization"
    )
    plan_rationale: str = Field(
        description="Overall architectural rationale for the planned transformation"
    )
