"""Schemas for the Quick Box (Spotlight) Dual-Result Optimization."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from prompt_optimizer.models.analysis import ClarificationQuestion, AmbiguityItem


class QuickOptimizeRequest(BaseModel):
    raw_prompt: str = Field(..., min_length=2, description="Raw unoptimized prompt")
    backend_type: str = Field(default="ollama", description="ollama | mock | gemini | openai")
    model_name: Optional[str] = Field(default=None)
    clarification_answers: Optional[Dict[str, str]] = Field(default=None)


class QuickCandidateResult(BaseModel):
    title: str = Field(description="'Concise (Fast & Lean)' or 'High Precision (Strict & Complete)'")
    prompt_text: str
    token_count: int
    token_delta: int
    reduction_percentage: float
    description: str
    preserved_invariants: List[str] = Field(default_factory=list)


class QuickOptimizeResponse(BaseModel):
    status: str = Field(description="'ready' or 'needs_clarification'")
    original_tokens: int
    
    # If needs_clarification
    ambiguities: List[AmbiguityItem] = Field(default_factory=list)
    clarification_questions: List[ClarificationQuestion] = Field(default_factory=list)
    
    # If ready: exactly 2 distinct results
    concise: Optional[QuickCandidateResult] = None
    high_precision: Optional[QuickCandidateResult] = None
