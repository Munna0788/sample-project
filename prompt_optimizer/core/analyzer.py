"""Prompt Analyzer Stage: Decomposes raw prompt into semantic components and invariants."""

import json
import logging
import re
from typing import Optional, Dict, Any, List

from prompt_optimizer.backends.base import BaseLLMBackend
from prompt_optimizer.models.analysis import (
    AnalysisResult,
    ExtractedRequirement,
    RequirementType,
    AmbiguityItem,
    ContradictionItem,
    RedundancyItem,
    ClarificationQuestion,
)

logger = logging.getLogger(__name__)

ANALYSIS_SYSTEM_PROMPT = """You are the Semantic Analyzer module of an Agentic Prompt Compiler.
Your duty is to dissect the user's raw prompt into its precise constituent components without inventing or dropping anything.

You MUST extract and separate:
1. Core task intent, operational context, constraints, desired output format, and tone.
2. Explicit vs Implicit requirements.
3. CRITICAL: Separate 'hard_requirements' (strict invariants that must NEVER be dropped) from 'soft_preferences' (stylistic guidelines).
4. Redundancies (repetitions, polite filler, no-ops).
5. Ambiguities & Contradictions.
6. Missing critical information and targeted clarification questions.

Return STRICT JSON complying with this structure:
{
  "task_intent": "string",
  "context": "string",
  "constraints": ["string"],
  "desired_output": "string",
  "tone_style": "string",
  "explicit_requirements": ["string"],
  "implicit_requirements": ["string"],
  "hard_requirements": [
    {"id": "REQ-01", "text": "string", "type": "hard", "category": "functional|constraint|format", "source_phrase": "string"}
  ],
  "soft_preferences": [
    {"id": "PREF-01", "text": "string", "type": "soft", "category": "style|optional", "source_phrase": "string"}
  ],
  "ambiguities": [
    {"id": "AMB-01", "description": "string", "possible_interpretations": ["string"], "suggested_resolution": "string"}
  ],
  "contradictions": [
    {"id": "CONTR-01", "description": "string", "conflicting_elements": ["string"], "recommended_fix": "string"}
  ],
  "redundant_instructions": [
    {"id": "RED-01", "phrase": "string", "reason": "string"}
  ],
  "missing_critical_info": ["string"],
  "clarification_questions": [
    {"id": "CLAR-01", "question": "string", "reason": "string", "default_assumption": "string", "suggested_options": ["option 1", "option 2"]}
  ]
}
"""


class PromptAnalyzer:
    """Dissects a raw prompt into semantic representations and invariants."""

    def __init__(self, backend: BaseLLMBackend):
        self.backend = backend

    def analyze(self, raw_prompt: str) -> AnalysisResult:
        """Execute deep analysis using the LLM backend."""
        user_message = f"""Analyze the following prompt and output the structured JSON analysis:

<ORIGINAL_PROMPT>
{raw_prompt}
</ORIGINAL_PROMPT>
"""
        response_text = self.backend.generate(
            prompt=user_message,
            system_instruction=ANALYSIS_SYSTEM_PROMPT,
            json_mode=True,
            temperature=0.1,
        )

        data = self._clean_and_parse_json(response_text)
        return AnalysisResult.model_validate(data)

    def _clean_and_parse_json(self, raw_str: str) -> Dict[str, Any]:
        """Strip markdown ticks and parse JSON safely using resilient repair."""
        from prompt_optimizer.utils.json_repair import extract_json
        parsed = extract_json(raw_str)
        if parsed and isinstance(parsed, dict) and "task_intent" in parsed:
            return parsed
        # Safe heuristic fallback
        return {
                "task_intent": "Execute provided prompt instructions",
                "context": "",
                "constraints": [],
                "desired_output": "Text output",
                "tone_style": "Standard",
                "explicit_requirements": ["Follow prompt"],
                "implicit_requirements": [],
                "hard_requirements": [
                    {
                        "id": "REQ-01",
                        "text": "Fulfill core user instructions",
                        "type": "hard",
                        "category": "functional",
                        "source_phrase": ""
                    }
                ],
                "soft_preferences": [],
                "ambiguities": [],
                "contradictions": [],
                "redundant_instructions": [],
                "missing_critical_info": [],
                "clarification_questions": []
            }
