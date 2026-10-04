"""Candidate Generator Stage: Synthesizes multiple distinct prompt architectures."""

import json
import logging
import re
from typing import List, Dict, Any

from prompt_optimizer.backends.base import BaseLLMBackend
from prompt_optimizer.models.analysis import AnalysisResult
from prompt_optimizer.models.plan import OptimizationPlan
from prompt_optimizer.models.candidate import PromptCandidate, CandidateStrategy
from prompt_optimizer.core.tokenizer import TokenizerEngine

logger = logging.getLogger(__name__)

GENERATOR_SYSTEM_PROMPT = """You are the Candidate Generator module of an Agentic Prompt Compiler.
Given the original prompt, semantic analysis, and optimization plan, you MUST generate THREE DISTINCT, HIGH-QUALITY CANDIDATE PROMPTS:

1. 'concise' (Maximum Compression):
   - Dense, token-minimalist, zero-filler.
   - Preserves all hard requirements as compact imperative bullets.
   - Ideal for saving maximum tokens while maintaining precision.

2. 'structured' (Hierarchical Markdown):
   - Professional prompt engineering layout: # Role, # Context, # Objective, # Constraints, # Output Schema.
   - Uses clear delimiters, markdown formatting, and explicit schemas.
   - Ideal for complex tasks needing maximum instruction following.

3. 'operational' (Production Edge-Case Framing):
   - Clarifies all detected ambiguities.
   - Provides explicit operational guardrails, edge-case directives, and strict failure prevention.
   - Focuses on zero-defect execution.

CRITICAL INVARIANT: You must NEVER drop any hard requirements in ANY candidate.

Return STRICT JSON complying with:
{
  "candidates": [
    {
      "id": "cand_concise",
      "strategy": "concise",
      "prompt_text": "string",
      "rationale": "string",
      "preserved_hard_requirements": ["string"],
      "changes_summary": ["string"]
    },
    {
      "id": "cand_structured",
      "strategy": "structured",
      "prompt_text": "string",
      "rationale": "string",
      "preserved_hard_requirements": ["string"],
      "changes_summary": ["string"]
    },
    {
      "id": "cand_operational",
      "strategy": "operational",
      "prompt_text": "string",
      "rationale": "string",
      "preserved_hard_requirements": ["string"],
      "changes_summary": ["string"]
    }
  ]
}
"""


class CandidateGenerator:
    """Produces multiple diverse optimization candidates."""

    def __init__(self, backend: BaseLLMBackend, tokenizer: TokenizerEngine):
        self.backend = backend
        self.tokenizer = tokenizer

    def generate_candidates(
        self,
        raw_prompt: str,
        analysis: AnalysisResult,
        plan: OptimizationPlan,
        original_token_count: int,
    ) -> List[PromptCandidate]:
        """Synthesize candidate prompts and measure their tokens deterministically."""
        hard_reqs = [f"{req.id}: {req.text}" for req in analysis.hard_requirements]

        prompt_payload = f"""<ORIGINAL_PROMPT>
{raw_prompt}
</ORIGINAL_PROMPT>

<TASK_INTENT>
{analysis.task_intent}
</TASK_INTENT>

<HARD_REQUIREMENT_INVARIANTS>
{json.dumps(hard_reqs, indent=2)}
</HARD_REQUIREMENT_INVARIANTS>

<OPTIMIZATION_PLAN>
Reorganization: {plan.reorganization_strategy}
Removals: {json.dumps(plan.removal_targets)}
Compressions: {json.dumps(plan.compression_targets)}
</OPTIMIZATION_PLAN>

Generate the 3 candidates in strict JSON.
"""
        response_text = self.backend.generate(
            prompt=prompt_payload,
            system_instruction=GENERATOR_SYSTEM_PROMPT,
            json_mode=True,
            temperature=0.3,
        )

        candidates_raw = self._clean_and_parse_json(response_text, raw_prompt, hard_reqs)
        candidates: List[PromptCandidate] = []

        for item in candidates_raw:
            p_text = item.get("prompt_text", "").strip()
            # Deterministic token measurement in pure Python
            tokens = self.tokenizer.measure(p_text, original_tokens=original_token_count)

            strategy_str = item.get("strategy", "concise").lower()
            try:
                strategy = CandidateStrategy(strategy_str)
            except ValueError:
                strategy = CandidateStrategy.CONCISE

            cand = PromptCandidate(
                id=item.get("id", f"cand_{strategy.value}"),
                strategy=strategy,
                prompt_text=p_text,
                tokens=tokens,
                rationale=item.get("rationale", "Optimized candidate"),
                preserved_hard_requirements=item.get("preserved_hard_requirements", [r.id for r in analysis.hard_requirements]),
                changes_summary=item.get("changes_summary", []),
            )
            candidates.append(cand)

        return candidates

    def _clean_and_parse_json(self, raw_str: str, raw_prompt: str, hard_reqs: list) -> List[Dict[str, Any]]:
        from prompt_optimizer.utils.json_repair import extract_json
        parsed = extract_json(raw_str)
        if parsed and isinstance(parsed, dict) and "candidates" in parsed:
            return parsed.get("candidates", [])
        return [
            {
                "id": "cand_concise",
                "strategy": "concise",
                "prompt_text": raw_prompt.strip(),
                "rationale": "Fallback concise prompt",
                "preserved_hard_requirements": hard_reqs,
                "changes_summary": ["Fallback pass"]
            }
        ]
