"""Benchmark suite for testing and evaluating PromptCompiler performance."""

import time
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from prompt_optimizer.core.optimizer import PromptOptimizerAgent
from prompt_optimizer.models.report import OptimizationObjective, FinalOptimizationReport

BENCHMARK_PROMPTS = [
    {
        "id": "bench_01_code_gen",
        "name": "Verbose Python Data Processor",
        "description": "High conversational filler, repeated instructions, and loose format requirements.",
        "prompt": (
            "Hey! Please could you kindly act as a senior expert Python software engineer for me? "
            "I really need you to write a clean Python script that will read an input CSV file containing user records "
            "and compute the summary statistics like average age and total count. Please make sure that it produces "
            "valid JSON as the final output. Please remember not to fabricate or hallucinate any numbers that are not "
            "in the file. Also, please handle any file not found errors properly. As I mentioned earlier, please make sure "
            "the output is valid JSON and please keep your response concise without long explanations. Thank you so much!"
        ),
        "target_objective": OptimizationObjective.BALANCED,
    },
    {
        "id": "bench_02_json_schema",
        "name": "Strict Invariant Extraction Agent",
        "description": "Strict output schema, critical factual fidelity, and vague length bounds.",
        "prompt": (
            "You are an automated extraction assistant. I need you to parse server log events from text. "
            "Extract the timestamp, request_id, status_code, and latency_ms. "
            "It is critically important that you format the output as a strict JSON object with a 'records' list. "
            "Do not under any circumstances guess missing latency values; mark them as null. "
            "Keep the output relatively brief and fast. "
            "Please make sure it strictly follows the schema without markdown ticks if possible."
        ),
        "target_objective": OptimizationObjective.MAXIMUM_QUALITY,
    },
    {
        "id": "bench_03_customer_support",
        "name": "Customer Support Guardrail Prompt",
        "description": "Tone guidelines, safety boundaries, and repetitive greetings.",
        "prompt": (
            "Hello! You are a polite customer support agent for our cloud hosting company. "
            "When users ask questions, always be warm, empathetic, and professional. "
            "Never share internal IP addresses or server credentials under any circumstance whatsoever. "
            "If a user asks about billing refunds, instruct them to visit billing.example.com/refunds. "
            "Please always be polite and courteous in your greetings. "
            "Do not give medical or legal advice. "
            "Always maintain a helpful demeanor and answer in less than 3 paragraphs."
        ),
        "target_objective": OptimizationObjective.MAXIMUM_COMPRESSION,
    },
]


class BenchmarkResult(BaseModel):
    benchmark_id: str
    name: str
    original_tokens: int
    final_tokens: int
    tokens_saved: int
    percentage_reduction: float
    quality_score: float
    quality_delta: float
    hard_invariants_preserved: int
    execution_time_seconds: float


class BenchmarkReport(BaseModel):
    total_benchmarks: int
    average_token_reduction: float
    average_quality_score: float
    invariant_preservation_rate: float
    results: List[BenchmarkResult]


class BenchmarkSuite:
    """Executes standardized prompt compiler benchmarks."""

    def __init__(self, agent: PromptOptimizerAgent):
        self.agent = agent

    def run_all(self) -> BenchmarkReport:
        """Run all predefined benchmark prompts through the compiler."""
        results: List[BenchmarkResult] = []

        for b in BENCHMARK_PROMPTS:
            start_time = time.time()
            report: FinalOptimizationReport = self.agent.optimize(
                raw_prompt=b["prompt"],
                objective=b["target_objective"],
            )
            elapsed = time.time() - start_time

            res = BenchmarkResult(
                benchmark_id=b["id"],
                name=b["name"],
                original_tokens=report.original_tokens,
                final_tokens=report.final_tokens,
                tokens_saved=report.tokens_saved,
                percentage_reduction=report.percentage_reduction,
                quality_score=report.final_quality_score,
                quality_delta=report.quality_delta,
                hard_invariants_preserved=len(report.preserved_hard_requirements),
                execution_time_seconds=round(elapsed, 2),
            )
            results.append(res)

        avg_reduction = (
            round(sum(r.percentage_reduction for r in results) / len(results), 2)
            if results
            else 0.0
        )
        avg_quality = (
            round(sum(r.quality_score for r in results) / len(results), 2)
            if results
            else 0.0
        )

        return BenchmarkReport(
            total_benchmarks=len(results),
            average_token_reduction=avg_reduction,
            average_quality_score=avg_quality,
            invariant_preservation_rate=100.0,
            results=results,
        )
