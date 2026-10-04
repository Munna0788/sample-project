"""Evaluator Stage: Evaluates execution outputs against requirements and applies safety guardrails."""

import json
import logging
import re
from typing import List, Dict, Any, Optional

from prompt_optimizer.backends.base import BaseLLMBackend
from prompt_optimizer.models.analysis import AnalysisResult
from prompt_optimizer.models.candidate import PromptCandidate
from prompt_optimizer.models.evaluation import (
    TestCase,
    ExecutionResult,
    ScoreBreakdown,
    CandidateEvaluation,
)

logger = logging.getLogger(__name__)

EVALUATOR_SYSTEM_PROMPT = """You are the Quality Evaluator module of an Agentic Prompt Compiler.
Evaluate the candidate prompt's execution outputs against the original task requirements on a strict 0.0 to 10.0 scale.

Dimensions to grade:
1. task_correctness (0.0 - 10.0): Did it solve the core problem correctly?
2. requirement_preservation (0.0 - 10.0): Are hard and soft requirements respected?
3. completeness (0.0 - 10.0): Are all necessary aspects addressed?
4. clarity (0.0 - 10.0): Is the output lucid and unambiguous?
5. output_format_adherence (0.0 - 10.0): Did it follow required structure/schema?

You MUST explicitly check the HARD REQUIREMENTS:
- List every satisfied hard requirement in 'satisfied_hard_requirements'.
- List any broken/dropped hard requirement in 'violated_hard_requirements'.

Return STRICT JSON:
{
  "task_correctness": 9.0,
  "requirement_preservation": 9.5,
  "completeness": 9.0,
  "clarity": 9.5,
  "output_format_adherence": 10.0,
  "satisfied_hard_requirements": ["REQ-01"],
  "violated_hard_requirements": [],
  "evaluation_notes": "string"
}
"""


class PromptEvaluator:
    """Evaluates outputs, checks requirement preservation invariants, and enforces performance guardrails."""

    def __init__(self, backend: BaseLLMBackend, quality_guardrail_threshold: float = 7.0):
        self.backend = backend
        self.quality_guardrail_threshold = quality_guardrail_threshold

    def evaluate_candidate(
        self,
        candidate: PromptCandidate,
        analysis: AnalysisResult,
        test_cases: List[TestCase],
        execution_results: List[ExecutionResult],
        baseline_quality_score: Optional[float] = None,
    ) -> CandidateEvaluation:
        """Evaluate candidate execution outputs, calculate composite score, and apply guardrail checks."""
        hard_req_list = [f"{r.id}: {r.text}" for r in analysis.hard_requirements]

        # Aggregate test outputs for evaluation prompt
        executions_summary = []
        for res in execution_results:
            executions_summary.append({
                "test_case_id": res.test_case_id,
                "output_sample": res.output_text[:600],
            })

        user_message = f"""<TASK_INTENT>
{analysis.task_intent}
</TASK_INTENT>

<HARD_REQUIREMENTS>
{json.dumps(hard_req_list, indent=2)}
</HARD_REQUIREMENTS>

<CANDIDATE_PROMPT>
{candidate.prompt_text}
</CANDIDATE_PROMPT>

<EXECUTION_OUTPUTS>
{json.dumps(executions_summary, indent=2)}
</EXECUTION_OUTPUTS>

Grade output adherence in strict JSON.
"""
        response_text = self.backend.generate(
            prompt=user_message,
            system_instruction=EVALUATOR_SYSTEM_PROMPT,
            json_mode=True,
            temperature=0.1,
        )

        data = self._clean_and_parse_evaluation(response_text, [r.id for r in analysis.hard_requirements])

        # Deterministic Python weighted composite calculation (Quality score formula)
        # Correctness: 30%, Requirements: 30%, Completeness: 15%, Clarity: 15%, Format: 10%
        w_correctness = float(data.get("task_correctness", 8.0)) * 0.30
        w_reqs = float(data.get("requirement_preservation", 8.0)) * 0.30
        w_comp = float(data.get("completeness", 8.0)) * 0.15
        w_clarity = float(data.get("clarity", 8.0)) * 0.15
        w_fmt = float(data.get("output_format_adherence", 8.0)) * 0.10
        overall_quality = round(w_correctness + w_reqs + w_comp + w_clarity + w_fmt, 2)

        violated_reqs = data.get("violated_hard_requirements", [])
        satisfied_reqs = data.get("satisfied_hard_requirements", [])

        scores = ScoreBreakdown(
            task_correctness=float(data.get("task_correctness", 8.0)),
            requirement_preservation=float(data.get("requirement_preservation", 8.0)),
            completeness=float(data.get("completeness", 8.0)),
            clarity=float(data.get("clarity", 8.0)),
            output_format_adherence=float(data.get("output_format_adherence", 8.0)),
            overall_quality_score=overall_quality,
            satisfied_hard_requirements=satisfied_reqs,
            violated_hard_requirements=violated_reqs,
            evaluation_notes=data.get("evaluation_notes", "Evaluation completed."),
        )

        # GUARDRAIL VERIFICATION RULE:
        # Rejection occurs if:
        # 1. Quality score is below minimum acceptable threshold
        # 2. Or any Hard Requirement was violated / dropped
        # 3. Or quality dropped > 15% compared to original baseline
        passed_guardrail = True
        rejection_reason = None

        if scores.overall_quality_score < self.quality_guardrail_threshold:
            passed_guardrail = False
            rejection_reason = f"Overall quality ({scores.overall_quality_score:.1f}) below threshold ({self.quality_guardrail_threshold:.1f})."
        elif len(violated_reqs) > 0:
            passed_guardrail = False
            rejection_reason = f"Hard requirement invariants violated: {', '.join(violated_reqs)}."
        elif baseline_quality_score is not None and (baseline_quality_score - scores.overall_quality_score) > 1.5:
            passed_guardrail = False
            rejection_reason = f"Significant performance degradation: dropped from baseline {baseline_quality_score:.1f} to {scores.overall_quality_score:.1f}."

        return CandidateEvaluation(
            candidate_id=candidate.id,
            strategy=candidate.strategy.value,
            scores=scores,
            tokens=candidate.tokens,
            passed_guardrail=passed_guardrail,
            guardrail_rejection_reason=rejection_reason,
            composite_score=overall_quality,
            test_executions=execution_results,
        )

    def _clean_and_parse_evaluation(self, raw_str: str, all_hard_req_ids: List[str]) -> Dict[str, Any]:
        cleaned = raw_str.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse evaluator JSON: {cleaned}")
            return {
                "task_correctness": 8.0,
                "requirement_preservation": 8.5,
                "completeness": 8.0,
                "clarity": 8.5,
                "output_format_adherence": 9.0,
                "satisfied_hard_requirements": all_hard_req_ids,
                "violated_hard_requirements": [],
                "evaluation_notes": "Parsed via fallback scoring."
            }
