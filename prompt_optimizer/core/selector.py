"""Candidate Selector Stage: Selects the optimal prompt according to configurable objectives."""

import logging
from typing import List, Tuple, Optional

from prompt_optimizer.models.evaluation import CandidateEvaluation
from prompt_optimizer.models.report import OptimizationObjective

logger = logging.getLogger(__name__)


class CandidateSelector:
    """Ranks and selects the winning candidate prompt based on objective functions."""

    def select(
        self,
        evaluations: List[CandidateEvaluation],
        objective: OptimizationObjective,
    ) -> Tuple[CandidateEvaluation, str]:
        """Select best candidate. Returns (winning_evaluation, explainable_rationale)."""
        if not evaluations:
            raise ValueError("No candidate evaluations provided for selection.")

        # Filter candidates that passed guardrails
        valid_candidates = [e for e in evaluations if e.passed_guardrail]

        # Safety Fallback: if all failed, pick the one with highest quality score with warning
        if not valid_candidates:
            fallback = max(evaluations, key=lambda e: e.scores.overall_quality_score)
            rationale = (
                f"SAFETY GUARDRAIL ALERT: All generated candidates were rejected by safety invariants. "
                f"Selecting highest-scoring candidate ({fallback.candidate_id}) as fallback, "
                f"rejection diagnostic: {fallback.guardrail_rejection_reason}"
            )
            return fallback, rationale

        if objective == OptimizationObjective.MAXIMUM_QUALITY:
            # Sort primarily by quality score, secondarily by token reduction
            best = max(
                valid_candidates,
                key=lambda e: (e.scores.overall_quality_score, e.tokens.reduction_percentage)
            )
            rationale = (
                f"Selected under 'maximum_quality' objective: Candidate '{best.candidate_id}' "
                f"achieved the highest quality score ({best.scores.overall_quality_score:.2f}/10.0) "
                f"while maintaining 100% hard requirement preservation and saving {best.tokens.reduction_percentage:.1f}% tokens."
            )
            return best, rationale

        elif objective == OptimizationObjective.MAXIMUM_COMPRESSION:
            # Sort primarily by token reduction, while satisfying the quality guardrail
            best = max(
                valid_candidates,
                key=lambda e: (e.tokens.reduction_percentage, e.scores.overall_quality_score)
            )
            rationale = (
                f"Selected under 'maximum_compression' objective: Candidate '{best.candidate_id}' "
                f"achieved the maximum token reduction ({best.tokens.reduction_percentage:.1f}%, saving {best.tokens.token_delta} tokens) "
                f"while passing all quality safety guardrails (Quality: {best.scores.overall_quality_score:.2f}/10.0)."
            )
            return best, rationale

        else:  # BALANCED
            # Pareto-optimal composite: 65% quality (normalized 0-1) + 35% token reduction (normalized 0-1)
            def compute_balanced_score(cand: CandidateEvaluation) -> float:
                q_norm = cand.scores.overall_quality_score / 10.0
                # Clamp token reduction between 0.0 and 1.0 (50% reduction = 0.50)
                t_norm = max(0.0, min(cand.tokens.reduction_percentage / 100.0, 1.0))
                return (0.65 * q_norm) + (0.35 * t_norm)

            for cand in valid_candidates:
                cand.composite_score = round(compute_balanced_score(cand) * 10.0, 2)

            best = max(valid_candidates, key=lambda e: e.composite_score)
            rationale = (
                f"Selected under 'balanced' objective: Candidate '{best.candidate_id}' "
                f"achieved the optimal Pareto balance (Composite: {best.composite_score:.2f}/10.0) "
                f"with {best.scores.overall_quality_score:.2f}/10.0 quality score and {best.tokens.reduction_percentage:.1f}% token reduction."
            )
            return best, rationale
