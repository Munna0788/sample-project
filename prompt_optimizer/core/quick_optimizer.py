"""Quick Optimizer Engine: Specialized for Spotlight/Overlay Dual-Result Execution."""

import json
import logging
from typing import Optional, Dict, Any, List

from prompt_optimizer.backends.base import BaseLLMBackend
from prompt_optimizer.models.analysis import AnalysisResult
from prompt_optimizer.models.quick import (
    QuickOptimizeResponse,
    QuickCandidateResult,
)
from prompt_optimizer.core.tokenizer import TokenizerEngine
from prompt_optimizer.core.analyzer import PromptAnalyzer

logger = logging.getLogger(__name__)

DUAL_SYNTHESIS_SYSTEM_PROMPT = """You are the Dual-Result Synthesis Engine of an Agentic Prompt Compiler.
You MUST generate EXACTLY TWO OPTIMIZED PROMPT VARIATIONS for the user:

Variation 1: 'concise' (Fast & Token-Lean):
- Keep it highly concise.
- Focus on brevity: eliminate conversational filler, trim soft stylistic nuances, and formulate direct imperative bullets.
- Preserves the primary task without excessive precision or verbose guardrails.
- Maximizes token reduction.

Variation 2: 'high_precision' (Strict & Complete):
- Much higher precision.
- Strictly preserve all hard requirements and domain invariants.
- Include structured sections (# Context, # Objective, # Hard Rules, # Output Schema).
- Provide explicit edge-case handling so the executing model never deviates or hallucinates.

Return STRICT JSON complying with this structure:
{
  "concise_prompt": "string",
  "concise_rationale": "string",
  "high_precision_prompt": "string",
  "high_precision_rationale": "string"
}
"""


from prompt_optimizer.core.cache import PromptCache

class QuickOptimizer:
    """Orchestrates quick dual-result prompt optimization with instant ambiguity querying."""

    def __init__(self, backend: BaseLLMBackend, tokenizer: Optional[TokenizerEngine] = None, cache: Optional[PromptCache] = None):
        self.backend = backend
        self.tokenizer = tokenizer or TokenizerEngine()
        self.analyzer = PromptAnalyzer(backend)
        self.cache = cache or PromptCache()

    def optimize_quick(
        self,
        raw_prompt: str,
        clarification_answers: Optional[Dict[str, str]] = None,
        force_generate: bool = False,
    ) -> QuickOptimizeResponse:
        """Run quick optimization. Halts on ambiguities if not clarified, otherwise returns dual results."""
        raw_text = raw_prompt.strip()

        # Check Cache
        cached_res = self.cache.get(raw_text, self.backend.get_model_name(), clarification_answers)
        if cached_res and not force_generate:
            return cached_res

        orig_metrics = self.tokenizer.measure(raw_text)
        orig_tokens = orig_metrics.token_count

        # Step 1: Semantic Analysis
        analysis: AnalysisResult = self.analyzer.analyze(raw_text)

        # Step 2: Check for ambiguities
        has_ambiguities = len(analysis.ambiguities) > 0 or len(analysis.clarification_questions) > 0
        clarified = bool(clarification_answers and len(clarification_answers) > 0)

        if has_ambiguities and not clarified and not force_generate:
            return QuickOptimizeResponse(
                status="needs_clarification",
                original_tokens=orig_tokens,
                ambiguities=analysis.ambiguities,
                clarification_questions=analysis.clarification_questions,
            )

        # Incorporate clarification answers if provided
        clarified_notes = []
        if clarification_answers:
            for q in analysis.clarification_questions:
                if q.id in clarification_answers:
                    q.user_answer = clarification_answers[q.id]
                    clarified_notes.append(f"User clarification ({q.id}): {q.user_answer}")

        # Step 3: Dual Synthesis (Concise vs High Precision)
        hard_reqs = [f"{r.id}: {r.text}" for r in analysis.hard_requirements]

        prompt_payload = f"""<ORIGINAL_PROMPT>
{raw_text}
</ORIGINAL_PROMPT>

<TASK_INTENT>
{analysis.task_intent}
</TASK_INTENT>

<HARD_INVARIANTS>
{json.dumps(hard_reqs)}
</HARD_INVARIANTS>

<CLARIFICATIONS>
{json.dumps(clarified_notes)}
</CLARIFICATIONS>

Synthesize both the 'concise' and 'high_precision' variations in strict JSON.
"""
        response_text = self.backend.generate(
            prompt=prompt_payload,
            system_instruction=DUAL_SYNTHESIS_SYSTEM_PROMPT,
            json_mode=True,
            temperature=0.2,
        )

        data = self._clean_and_parse(response_text, raw_text)

        concise_text = data.get("concise_prompt", raw_text).strip()
        high_precision_text = data.get("high_precision_prompt", raw_text).strip()

        # Deterministic Token Measurements
        concise_metrics = self.tokenizer.measure(concise_text, original_tokens=orig_tokens)
        hp_metrics = self.tokenizer.measure(high_precision_text, original_tokens=orig_tokens)

        concise_result = QuickCandidateResult(
            title="Concise (Fast & Lean)",
            prompt_text=concise_text,
            token_count=concise_metrics.token_count,
            token_delta=concise_metrics.token_delta,
            reduction_percentage=concise_metrics.reduction_percentage,
            description=data.get("concise_rationale", "Minimalist imperative directives, trims soft nuances to save maximum tokens."),
            preserved_invariants=[r.id for r in analysis.hard_requirements[:2]],
        )

        hp_result = QuickCandidateResult(
            title="High Precision (Strict & Complete)",
            prompt_text=high_precision_text,
            token_count=hp_metrics.token_count,
            token_delta=hp_metrics.token_delta,
            reduction_percentage=hp_metrics.reduction_percentage,
            description=data.get("high_precision_rationale", "Maximum instruction fidelity, explicit output schema, and strict failure guardrails."),
            preserved_invariants=[r.id for r in analysis.hard_requirements],
        )

        final_resp = QuickOptimizeResponse(
            status="ready",
            original_tokens=orig_tokens,
            ambiguities=analysis.ambiguities,
            clarification_questions=analysis.clarification_questions,
            concise=concise_result,
            high_precision=hp_result,
        )
        self.cache.set(raw_text, self.backend.get_model_name(), final_resp, clarification_answers)
        return final_resp

    def _clean_and_parse(self, raw_str: str, original_prompt: str) -> Dict[str, Any]:
        from prompt_optimizer.utils.json_repair import extract_json
        parsed = extract_json(raw_str)
        if parsed and "concise_prompt" in parsed and "high_precision_prompt" in parsed:
            return parsed

        # Robust heuristic fallback
        return {
            "concise_prompt": f"Fulfill task directly:\n{original_prompt.strip()}",
            "concise_rationale": "Compact directive without conversational filler.",
            "high_precision_prompt": f"# Objective\n{original_prompt.strip()}\n\n# Constraints\n- Output strictly valid formatting\n- Preserve all invariants without assumption",
            "high_precision_rationale": "Structured format with explicit guardrails."
        }
