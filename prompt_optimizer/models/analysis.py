"""Analysis schemas for the Prompt Optimization System."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class RequirementType(str, Enum):
    """Categorization of a requirement to prevent dropping critical constraints."""
    HARD = "hard"       # Invariants that MUST NOT be removed under any compression
    SOFT = "soft"       # Stylistic preferences, suggestions, or non-essential phrasing


class ExtractedRequirement(BaseModel):
    """A granular requirement extracted from the raw prompt."""
    id: str = Field(description="Unique identifier, e.g., REQ-01")
    text: str = Field(description="Normalized requirement statement")
    type: RequirementType = Field(description="Hard requirement or soft preference")
    category: str = Field(default="functional", description="functional, constraint, format, style, persona")
    source_phrase: Optional[str] = Field(default=None, description="Verbatim or near-verbatim excerpt from original prompt")


class AmbiguityItem(BaseModel):
    """Detected ambiguity in the raw prompt."""
    id: str = Field(description="e.g., AMB-01")
    description: str = Field(description="What is ambiguous")
    possible_interpretations: List[str] = Field(default_factory=list, description="Different ways to interpret this")
    suggested_resolution: str = Field(description="Recommended resolution assumption")


class ContradictionItem(BaseModel):
    """Contradiction or conflicting instruction detected in the prompt."""
    id: str = Field(description="e.g., CONTR-01")
    description: str = Field(description="Nature of the conflict")
    conflicting_elements: List[str] = Field(default_factory=list, description="The conflicting statements")
    recommended_fix: str = Field(description="How to reconcile the conflict")


class RedundancyItem(BaseModel):
    """Redundant, repeating, or filler text detected."""
    id: str = Field(description="e.g., RED-01")
    phrase: str = Field(description="Verbose or repeated phrase")
    reason: str = Field(description="Why this is redundant or token-wasteful")


class ClarificationQuestion(BaseModel):
    """Targeted clarification question to ask user before finalizing optimization."""
    id: str = Field(description="e.g., CLAR-01")
    question: str = Field(description="The question to clarify intent")
    reason: str = Field(description="Why this information is critical")
    default_assumption: str = Field(description="Assumption used if user does not answer")
    user_answer: Optional[str] = Field(default=None, description="User provided answer, if any")


class AnalysisResult(BaseModel):
    """Comprehensive semantic breakdown of the raw prompt."""
    task_intent: str = Field(description="Core task or overarching goal")
    context: str = Field(default="", description="Domain or operational background")
    constraints: List[str] = Field(default_factory=list, description="Explicit boundaries and limitations")
    desired_output: str = Field(description="Expected format, artifact, or response structure")
    tone_style: str = Field(default="objective", description="Expected tone, voice, or style")
    
    explicit_requirements: List[str] = Field(default_factory=list, description="Directly stated requirements")
    implicit_requirements: List[str] = Field(default_factory=list, description="Inferred technical/domain requirements")
    
    hard_requirements: List[ExtractedRequirement] = Field(
        default_factory=list,
        description="Critical constraints that must be preserved at 100% fidelity"
    )
    soft_preferences: List[ExtractedRequirement] = Field(
        default_factory=list,
        description="Flexible stylistic or secondary preferences"
    )
    
    ambiguities: List[AmbiguityItem] = Field(default_factory=list)
    contradictions: List[ContradictionItem] = Field(default_factory=list)
    redundant_instructions: List[RedundancyItem] = Field(default_factory=list)
    
    missing_critical_info: List[str] = Field(default_factory=list, description="Gaps in the prompt")
    clarification_questions: List[ClarificationQuestion] = Field(default_factory=list)
