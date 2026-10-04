"""Deterministic Mock LLM Backend for testing, simulation, and offline hackathon demos."""

import json
import re
from typing import Optional, Dict, Any

from prompt_optimizer.backends.base import BaseLLMBackend


class MockLLMBackend(BaseLLMBackend):
    """Provides structured, deterministic mock responses for all compiler stages."""

    def __init__(self, model: str = "mock-agentic-v1"):
        self.model = model

    def is_available(self) -> bool:
        return True

    def get_model_name(self) -> str:
        return f"mock/{self.model}"

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> str:
        lower_prompt = prompt.lower()

        # Stage 1: Analysis Prompt
        if "analyze the following prompt" in lower_prompt or "extraction" in lower_prompt:
            return json.dumps({
                "task_intent": "Analyze input data and generate structured output according to requirements",
                "context": "Data processing and automated agent execution",
                "constraints": [
                    "Preserve all key facts accurately",
                    "Do not include unnecessary conversational filler"
                ],
                "desired_output": "Structured Markdown report with bullet points and code block",
                "tone_style": "Clear, concise, professional technical tone",
                "explicit_requirements": [
                    "Extract primary metrics",
                    "List errors in order",
                    "Produce valid JSON output"
                ],
                "implicit_requirements": [
                    "Handle empty inputs gracefully",
                    "Deterministic format"
                ],
                "hard_requirements": [
                    {
                        "id": "REQ-01",
                        "text": "Produce strictly valid JSON with required summary keys",
                        "type": "hard",
                        "category": "format",
                        "source_phrase": "Must be valid JSON"
                    },
                    {
                        "id": "REQ-02",
                        "text": "Never fabricate or hallucinate omitted metrics",
                        "type": "hard",
                        "category": "functional",
                        "source_phrase": "Do not make up facts"
                    }
                ],
                "soft_preferences": [
                    {
                        "id": "PREF-01",
                        "text": "Friendly greeting if possible",
                        "type": "soft",
                        "category": "style",
                        "source_phrase": "Be polite"
                    }
                ],
                "ambiguities": [
                    {
                        "id": "AMB-01",
                        "description": "Output length not quantified ('keep it short')",
                        "possible_interpretations": ["Under 100 words", "Summary bullets only"],
                        "suggested_resolution": "Specify under 150 words"
                    }
                ],
                "contradictions": [],
                "redundant_instructions": [
                    {
                        "id": "RED-01",
                        "phrase": "Please please make sure to always remember to do this carefully",
                        "reason": "Conversational fluff repeating instruction"
                    }
                ],
                "missing_critical_info": [],
                "clarification_questions": [
                    {
                        "id": "CLAR-01",
                        "question": "What is the maximum allowed token length for the output?",
                        "reason": "Vague length constraint causes variance",
                        "default_assumption": "Target <= 200 tokens output"
                    }
                ]
            })

        # Stage 2: Planning Prompt
        if "optimization plan" in lower_prompt or "transformation plan" in lower_prompt:
            return json.dumps({
                "compression_targets": [
                    "Condense multi-sentence instructions into direct imperative bullet points",
                    "Eliminate polite filler and redundant caveats"
                ],
                "removal_targets": [
                    "Conversational greetings and excessive repetitions",
                    "Redundant 'as stated above' references"
                ],
                "merge_targets": [
                    "Combine formatting requirements and schema constraints into a single section"
                ],
                "reorganization_strategy": "Adopt standard Agent Protocol: Context -> Task -> Constraints -> Output Format",
                "hard_requirement_invariants": [
                    "REQ-01: Produce strictly valid JSON with required summary keys",
                    "REQ-02: Never fabricate or hallucinate omitted metrics"
                ],
                "planned_actions": [
                    {
                        "action_type": "REMOVE",
                        "target": "Polite conversational fluff",
                        "replacement": "",
                        "rationale": "Saves tokens without impacting task execution"
                    },
                    {
                        "action_type": "REORGANIZE",
                        "target": "Unstructured paragraph",
                        "replacement": "Role / Constraints / Output Format headings",
                        "rationale": "Improves LLM instruction following"
                    }
                ],
                "plan_rationale": "Refactor into dense imperative structure preserving all hard constraints."
            })

        # Stage 3: Candidate Generation Prompt
        if "candidate" in lower_prompt:
            return json.dumps({
                "candidates": [
                    {
                        "id": "cand_concise",
                        "strategy": "concise",
                        "prompt_text": "Extract metrics and errors from input data.\n- Output: Strict JSON only\n- Rule 1: Valid JSON with 'summary' and 'errors' keys\n- Rule 2: Never hallucinate missing data\n- Length: Under 150 words.",
                        "rationale": "High token compression removing conversational filler and structuring requirements as direct imperatives.",
                        "preserved_hard_requirements": ["REQ-01", "REQ-02"],
                        "changes_summary": ["Removed conversational boilerplate", "Compressed rules into bullet points"]
                    },
                    {
                        "id": "cand_structured",
                        "strategy": "structured",
                        "prompt_text": "# Role\nData Extraction Specialist\n\n# Objective\nExtract metrics and errors accurately from input data.\n\n# Constraints\n1. Output format: Valid JSON only.\n2. Invariant: Do not fabricate unverified metrics.\n3. Brevity: Keep explanations under 150 words.\n\n# Output Schema\n```json\n{\"summary\": {}, \"errors\": []}\n```",
                        "rationale": "Hierarchical Markdown architecture optimizing prompt comprehension and structural adherence.",
                        "preserved_hard_requirements": ["REQ-01", "REQ-02"],
                        "changes_summary": ["Organized into clear sections", "Included explicit JSON schema delimiter"]
                    },
                    {
                        "id": "cand_operational",
                        "strategy": "operational",
                        "prompt_text": "You are an automated extraction agent.\nTask: Extract key metrics and errors from the input.\nHard Rules:\n1. Return purely valid JSON with keys: summary, errors. No pre-text or markdown formatting outside JSON.\n2. Do not hallucinate or guess any metrics not explicitly present.\nEdge Cases:\n- If data is missing or empty, output {\"summary\": null, \"errors\": [\"Empty dataset\"]}.",
                        "rationale": "Operational framing clarifying edge cases and strict execution invariants.",
                        "preserved_hard_requirements": ["REQ-01", "REQ-02"],
                        "changes_summary": ["Explicit edge case handling", "Reinforced strict output invariant"]
                    }
                ]
            })

        # Stage 4: Test Case Generation
        if "test scenario" in lower_prompt or "test case" in lower_prompt:
            return json.dumps({
                "test_cases": [
                    {
                        "id": "TC-01",
                        "name": "Standard Data Extraction",
                        "input_scenario": "Log stream with 4 requests and 1 timeout error.",
                        "expected_behavior": "Returns JSON with summary count 4 and 1 recorded error."
                    },
                    {
                        "id": "TC-02",
                        "name": "Missing Data Edge Case",
                        "input_scenario": "Empty log file with no events.",
                        "expected_behavior": "Handles empty input without hallucinating records."
                    }
                ]
            })

        # Stage 5: Evaluation Prompt
        if "grade output" in lower_prompt or "evaluat" in lower_prompt:
            return json.dumps({
                "task_correctness": 9.5,
                "requirement_preservation": 9.8,
                "completeness": 9.2,
                "clarity": 9.6,
                "output_format_adherence": 10.0,
                "overall_quality_score": 9.6,
                "satisfied_hard_requirements": ["REQ-01", "REQ-02"],
                "violated_hard_requirements": [],
                "evaluation_notes": "Prompt produced compliant, high-precision output with zero invariant violations."
            })

        # Default fallback
        if json_mode:
            return json.dumps({"status": "success", "content": "Processed mock prompt."})
        return "Standard deterministic output generated by MockLLMBackend."
