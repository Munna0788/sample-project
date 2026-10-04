"""Optimization Planner Stage: Formulates an explainable transformation strategy."""

import json
import logging
import re
from typing import Dict, Any

from prompt_optimizer.backends.base import BaseLLMBackend
from prompt_optimizer.models.analysis import AnalysisResult
from prompt_optimizer.models.plan import OptimizationPlan

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = """You are the Optimization Planner module of an Agentic Prompt Compiler.
Your goal is to formulate a precise, explainable transformation plan to compress and restructure a prompt without dropping ANY hard requirements.

Based on the semantic analysis provided:
1. Identify compression targets (phrases that can be stated in far fewer tokens).
2. Identify removal targets (filler, greetings, duplicate instructions).
3. Identify merge targets (overlapping or scattered constraints to consolidate).
4. Specify a clear reorganization strategy (e.g. Role, Context, Objective, Constraints, Output Schema).
5. Explicitly list the hard requirements that must remain 100% intact as invariants.
6. Detail granular planned actions with reasons.

Return STRICT JSON:
{
  "compression_targets": ["string"],
  "removal_targets": ["string"],
  "merge_targets": ["string"],
  "reorganization_strategy": "string",
  "hard_requirement_invariants": ["string"],
  "planned_actions": [
    {
      "action_type": "COMPRESS|REMOVE|MERGE|REORGANIZE|CLARIFY",
      "target": "string",
      "replacement": "string",
      "rationale": "string"
    }
  ],
  "plan_rationale": "string"
}
"""


class OptimizationPlanner:
    """Creates a verifiable optimization blueprint before generating candidate prompts."""

    def __init__(self, backend: BaseLLMBackend):
        self.backend = backend

    def create_plan(self, raw_prompt: str, analysis: AnalysisResult) -> OptimizationPlan:
        """Generate an optimization plan given the raw prompt and its semantic analysis."""
        hard_req_summaries = [f"{req.id}: {req.text}" for req in analysis.hard_requirements]
        redundancies = [f"{r.phrase} (reason: {r.reason})" for r in analysis.redundant_instructions]

        prompt_payload = f"""<ORIGINAL_PROMPT>
{raw_prompt}
</ORIGINAL_PROMPT>

<SEMANTIC_ANALYSIS>
Task Intent: {analysis.task_intent}
Context: {analysis.context}
Desired Output: {analysis.desired_output}
Hard Requirements (MUST KEEP): {json.dumps(hard_req_summaries)}
Detected Redundancies: {json.dumps(redundancies)}
Ambiguities: {json.dumps([a.description for a in analysis.ambiguities])}
</SEMANTIC_ANALYSIS>

Produce the Optimization Plan in strict JSON.
"""
        response_text = self.backend.generate(
            prompt=prompt_payload,
            system_instruction=PLANNER_SYSTEM_PROMPT,
            json_mode=True,
            temperature=0.1,
        )

        data = self._clean_and_parse_json(response_text, hard_req_summaries)
        return OptimizationPlan.model_validate(data)

    def _clean_and_parse_json(self, raw_str: str, hard_reqs: list) -> Dict[str, Any]:
        from prompt_optimizer.utils.json_repair import extract_json
        parsed = extract_json(raw_str)
        if parsed and isinstance(parsed, dict) and "reorganization_strategy" in parsed:
            return parsed
        return {
            "compression_targets": ["Verbose phrasing"],
            "removal_targets": ["Conversational filler"],
            "merge_targets": ["Scattered requirements"],
            "reorganization_strategy": "Structural Markdown sections",
            "hard_requirement_invariants": hard_reqs,
            "planned_actions": [],
            "plan_rationale": "Standard compression while retaining invariants."
        }
