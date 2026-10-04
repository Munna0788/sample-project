"""Master Orchestrator: The Prompt Compiler / Optimization Agent."""

import logging
from typing import Optional, Dict, Any, List, Callable

from prompt_optimizer.backends.base import BaseLLMBackend
from prompt_optimizer.models.analysis import AnalysisResult, ClarificationQuestion
from prompt_optimizer.models.plan import OptimizationPlan
from prompt_optimizer.models.candidate import PromptCandidate
from prompt_optimizer.models.evaluation import (
    TestCase,
    ExecutionResult,
    CandidateEvaluation,
    ScoreBreakdown,
)
from prompt_optimizer.models.report import (
    OptimizationObjective,
    OptimizationIterationLog,
    FinalOptimizationReport,
)
from prompt_optimizer.core.tokenizer import TokenizerEngine
from prompt_optimizer.core.analyzer import PromptAnalyzer
from prompt_optimizer.core.planner import OptimizationPlanner
from prompt_optimizer.core.generator import CandidateGenerator
from prompt_optimizer.core.tester import PromptTester
from prompt_optimizer.core.evaluator import PromptEvaluator
from prompt_optimizer.core.refiner import CandidateRefiner
from prompt_optimizer.core.selector import CandidateSelector

logger = logging.getLogger(__name__)


class PromptOptimizerAgent:
    """The Agentic Prompt Compiler.
    
    Coordinates analysis, planning, multi-candidate generation, deterministic token measurement,
    test scenario execution, multi-dimensional evaluation, safety guardrail enforcement,
    iterative refinement, and explainable candidate selection.
    """

    def __init__(
        self,
        backend: BaseLLMBackend,
        tokenizer: Optional[TokenizerEngine] = None,
        quality_guardrail_threshold: float = 7.0,
        max_refinement_iterations: int = 1,
    ):
        self.backend = backend
        self.tokenizer = tokenizer or TokenizerEngine()
        self.quality_guardrail_threshold = quality_guardrail_threshold
        self.max_refinement_iterations = max_refinement_iterations

        # Stages
        self.analyzer = PromptAnalyzer(backend)
        self.planner = OptimizationPlanner(backend)
        self.generator = CandidateGenerator(backend, self.tokenizer)
        self.tester = PromptTester(backend)
        self.evaluator = PromptEvaluator(backend, quality_guardrail_threshold)
        self.refiner = CandidateRefiner(backend, self.tokenizer)
        self.selector = CandidateSelector()

    def optimize(
        self,
        raw_prompt: str,
        objective: OptimizationObjective = OptimizationObjective.BALANCED,
        clarification_answers: Optional[Dict[str, str]] = None,
        progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> FinalOptimizationReport:
        """Run the end-to-end prompt compiler optimization pipeline."""
        def emit_progress(stage: str, details: Dict[str, Any]):
            if progress_callback:
                progress_callback(stage, details)

        emit_progress("START", {"message": "Starting prompt optimization pipeline..."})

        # Step 1: Measure Original Prompt Tokens deterministically
        orig_tokens_metric = self.tokenizer.measure(raw_prompt)
        orig_token_count = orig_tokens_metric.token_count
        emit_progress("TOKEN_COUNT", {"original_tokens": orig_token_count})

        # Step 2: Semantic Analysis & Invariant Separation
        emit_progress("ANALYSIS", {"message": "Analyzing prompt semantics and invariants..."})
        analysis = self.analyzer.analyze(raw_prompt)

        # Incorporate user clarification answers if provided
        if clarification_answers:
            for q in analysis.clarification_questions:
                if q.id in clarification_answers:
                    q.user_answer = clarification_answers[q.id]
                    # Append clarified answer to explicit requirements
                    analysis.explicit_requirements.append(
                        f"Clarification ({q.id}): {q.user_answer}"
                    )

        emit_progress("ANALYSIS_COMPLETE", {
            "hard_requirements_count": len(analysis.hard_requirements),
            "soft_preferences_count": len(analysis.soft_preferences),
            "redundancies_count": len(analysis.redundant_instructions),
            "ambiguities_count": len(analysis.ambiguities),
        })

        # Step 3: Transformation Planning
        emit_progress("PLANNING", {"message": "Constructing optimization transformation plan..."})
        plan = self.planner.create_plan(raw_prompt, analysis)
        emit_progress("PLANNING_COMPLETE", {"reorganization": plan.reorganization_strategy})

        # Step 4: Multi-Candidate Generation
        emit_progress("GENERATION", {"message": "Generating diverse candidate architectures..."})
        candidates = self.generator.generate_candidates(
            raw_prompt=raw_prompt,
            analysis=analysis,
            plan=plan,
            original_token_count=orig_token_count,
        )
        emit_progress("GENERATION_COMPLETE", {"candidate_count": len(candidates)})

        # Step 5: Test Case Generation
        emit_progress("TEST_GEN", {"message": "Synthesizing test scenarios from task intent..."})
        test_cases = self.tester.generate_test_cases(raw_prompt, analysis)
        emit_progress("TEST_GEN_COMPLETE", {"test_case_count": len(test_cases)})

        # Step 6: Simulate Baseline (Original Prompt) on Test Cases
        emit_progress("BASELINE_EXEC", {"message": "Executing original baseline prompt..."})
        baseline_results: List[ExecutionResult] = []
        for tc in test_cases:
            res = self.tester.execute_prompt(raw_prompt, "original", tc)
            baseline_results.append(res)

        # Evaluate baseline quality
        baseline_dummy_candidate = PromptCandidate(
            id="original",
            strategy="concise",  # placeholder
            prompt_text=raw_prompt,
            tokens=orig_tokens_metric,
            rationale="Original baseline prompt",
        )
        baseline_eval = self.evaluator.evaluate_candidate(
            candidate=baseline_dummy_candidate,
            analysis=analysis,
            test_cases=test_cases,
            execution_results=baseline_results,
        )
        baseline_quality = baseline_eval.scores.overall_quality_score
        emit_progress("BASELINE_EVAL", {"baseline_quality_score": baseline_quality})

        # Step 7: Simulate Candidates & Evaluate
        emit_progress("CANDIDATE_EXEC", {"message": "Executing and evaluating candidates..."})
        candidate_evaluations: List[CandidateEvaluation] = []
        candidate_dict: Dict[str, PromptCandidate] = {c.id: c for c in candidates}

        for cand in candidates:
            cand_results = []
            for tc in test_cases:
                res = self.tester.execute_prompt(cand.prompt_text, cand.id, tc)
                cand_results.append(res)

            eval_res = self.evaluator.evaluate_candidate(
                candidate=cand,
                analysis=analysis,
                test_cases=test_cases,
                execution_results=cand_results,
                baseline_quality_score=baseline_quality,
            )
            candidate_evaluations.append(eval_res)

        # Step 8: Iterative Refinement Loop (if needed)
        iteration_logs: List[OptimizationIterationLog] = []
        current_best = max(candidate_evaluations, key=lambda e: e.scores.overall_quality_score)
        iteration_logs.append(OptimizationIterationLog(
            iteration=1,
            candidates_tested=len(candidates),
            best_candidate_id=current_best.candidate_id,
            best_quality_score=current_best.scores.overall_quality_score,
            notes="Initial candidate batch evaluated."
        ))

        # Check if refinement is needed (e.g., if best candidate failed guardrail or dropped a req)
        if not current_best.passed_guardrail and self.max_refinement_iterations > 0:
            emit_progress("REFINEMENT", {"message": f"Refining candidate {current_best.candidate_id}..."})
            for iter_idx in range(self.max_refinement_iterations):
                source_candidate = candidate_dict.get(current_best.candidate_id, candidates[0])
                refined_candidate = self.refiner.refine(
                    candidate=source_candidate,
                    evaluation=current_best,
                    analysis=analysis,
                    original_token_count=orig_token_count,
                    iteration_number=iter_idx + 1,
                )
                candidate_dict[refined_candidate.id] = refined_candidate

                # Execute refined candidate
                refined_results = [
                    self.tester.execute_prompt(refined_candidate.prompt_text, refined_candidate.id, tc)
                    for tc in test_cases
                ]
                refined_eval = self.evaluator.evaluate_candidate(
                    candidate=refined_candidate,
                    analysis=analysis,
                    test_cases=test_cases,
                    execution_results=refined_results,
                    baseline_quality_score=baseline_quality,
                )
                candidate_evaluations.append(refined_eval)

                iteration_logs.append(OptimizationIterationLog(
                    iteration=iter_idx + 2,
                    candidates_tested=1,
                    best_candidate_id=refined_eval.candidate_id,
                    best_quality_score=refined_eval.scores.overall_quality_score,
                    notes=f"Refinement applied: {refined_eval.guardrail_rejection_reason or 'Passed guardrails.'}"
                ))

                if refined_eval.passed_guardrail:
                    break

        # Step 9: Multi-Objective Selection
        emit_progress("SELECTION", {"message": f"Selecting optimal prompt under objective: {objective.value}..."})
        winner_eval, selection_rationale = self.selector.select(
            evaluations=candidate_evaluations,
            objective=objective,
        )

        winning_candidate = candidate_dict.get(winner_eval.candidate_id)
        if winning_candidate is None:
            # Fallback if lookup misses
            final_prompt_text = raw_prompt
            final_token_count = orig_token_count
        else:
            final_prompt_text = winning_candidate.prompt_text
            final_token_count = winner_eval.tokens.token_count

        tokens_saved = orig_token_count - final_token_count
        pct_reduction = round((tokens_saved / orig_token_count * 100.0), 2) if orig_token_count > 0 else 0.0
        final_quality = winner_eval.scores.overall_quality_score
        quality_delta = round(final_quality - baseline_quality, 2)

        # Step 10: Compile Final Optimization Report
        report = FinalOptimizationReport(
            original_prompt=raw_prompt,
            final_optimized_prompt=final_prompt_text,
            original_tokens=orig_token_count,
            final_tokens=final_token_count,
            tokens_saved=tokens_saved,
            percentage_reduction=pct_reduction,
            original_quality_score=baseline_quality,
            final_quality_score=final_quality,
            quality_delta=quality_delta,
            preserved_hard_requirements=[f"{r.id}: {r.text}" for r in analysis.hard_requirements],
            preserved_soft_preferences=[f"{r.id}: {r.text}" for r in analysis.soft_preferences],
            removed_redundancies=[f"{r.phrase} ({r.reason})" for r in analysis.redundant_instructions],
            detected_ambiguities=[a.description for a in analysis.ambiguities],
            optimization_iterations=len(iteration_logs),
            iteration_history=iteration_logs,
            selection_objective=objective,
            selected_candidate_id=winner_eval.candidate_id,
            selection_rationale=selection_rationale,
            all_candidates=candidate_evaluations,
        )

        emit_progress("COMPLETE", {"report": report.model_dump()})
        return report
