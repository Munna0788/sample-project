"""Iterative Refinement Stage: Heals rejected or suboptimal candidates based on evaluator diagnostics."""

import json
import logging
import re
from typing import Optional, List

from prompt_optimizer.backends.base import BaseLLMBackend
from prompt_optimizer.models.analysis import AnalysisResult
from prompt_optimizer.models.candidate import PromptCandidate, CandidateStrategy
from prompt_optimizer.models.evaluation import CandidateEvaluation
from prompt_optimizer.core.tokenizer import TokenizerEngine

logger = logging.getLogger(__name__)

REFINER_SYSTEM_PROMPT = """You are the Refinement Specialist module of an Agentic Prompt Compiler.
You are given a candidate prompt that had issues or was rejected during evaluation (e.g. dropped a requirement, ambiguous phrasing, or format deviation).

Your mission:
1. Retain the structural elegance and token savings of the candidate.
2. Fix the exact failure identified in the evaluator diagnostics.
3. Explicitly restore any missing hard requirements.

Return STRICT JSON:
{
  "refined_prompt": "string",
  "rationale": "string",
  "fixed_issues": ["string"]
}
"""


class CandidateRefiner:
    """Iteratively refines a candidate prompt using diagnostic feedback."""

    def __init__(self, backend: BaseLLMBackend, tokenizer: TokenizerEngine):
        self.backend = backend
        self.tokenizer = tokenizer

    def refine(
        self,
        candidate: PromptCandidate,
        evaluation: CandidateEvaluation,
        analysis: AnalysisResult,
        original_token_count: int,
        iteration_number: int,
    ) -> PromptCandidate:
        """Produce a healed and refined candidate prompt."""
        diagnostic = evaluation.guardrail_rejection_reason or evaluation.scores.evaluation_notes
        hard_reqs = [f"{r.id}: {r.text}" for r in analysis.hard_requirements]

        prompt_payload = f"""<CANDIDATE_TO_REFINE>
{candidate.prompt_text}
</CANDIDATE_TO_REFINE>

<EVALUATION_DIAGNOSTICS>
Violation / Feedback: {diagnostic}
Violated Hard Requirements: {evaluation.scores.violated_hard_requirements}
</EVALUATION_DIAGNOSTICS>

<REQUIRED_HARD_INVARIANTS>
{json.dumps(hard_reqs, indent=2)}
</REQUIRED_HARD_INVARIANTS>

Generate the healed and refined prompt in strict JSON.
"""
        response_text = self.backend.generate(
            prompt=prompt_payload,
            system_instruction=REFINER_SYSTEM_PROMPT,
            json_mode=True,
            temperature=0.2,
        )

        data = self._clean_and_parse(response_text, candidate.prompt_text)
        refined_text = data.get("refined_prompt", candidate.prompt_text).strip()
        tokens = self.tokenizer.measure(refined_text, original_tokens=original_token_count)

        return PromptCandidate(
            id=f"{candidate.id}_v{iteration_number + 1}",
            strategy=candidate.strategy,
            prompt_text=refined_text,
            tokens=tokens,
            rationale=f"Refined (Iter {iteration_number + 1}): {data.get('rationale', 'Repaired invariant')}",
            preserved_hard_requirements=[r.id for r in analysis.hard_requirements],
            changes_summary=data.get("fixed_issues", ["Restored hard constraints"]),
        )

    def _clean_and_parse(self, raw_str: str, fallback_text: str):
        cleaned = raw_str.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {
                "refined_prompt": fallback_text,
                "rationale": "Fallback during refinement",
                "fixed_issues": []
            }
