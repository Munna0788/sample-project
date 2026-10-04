"""Test Case Generation and Execution Stage: Generates realistic test scenarios and simulates prompts."""

import json
import logging
import re
import time
from typing import List, Dict, Any

from prompt_optimizer.backends.base import BaseLLMBackend
from prompt_optimizer.models.analysis import AnalysisResult
from prompt_optimizer.models.candidate import PromptCandidate
from prompt_optimizer.models.evaluation import TestCase, ExecutionResult

logger = logging.getLogger(__name__)

TEST_GEN_SYSTEM_PROMPT = """You are the Test Suite Generator module of an Agentic Prompt Compiler.
Generate 2 realistic, rigorous test scenarios to evaluate how well prompts perform their stated task.

Each test case must include:
1. 'id': e.g. "TC-01"
2. 'name': short title
3. 'input_scenario': realistic input data or query representing caller input
4. 'expected_behavior': clear criteria for what must be produced or satisfied based on original requirements.

Return STRICT JSON:
{
  "test_cases": [
    {
      "id": "TC-01",
      "name": "string",
      "input_scenario": "string",
      "expected_behavior": "string"
    }
  ]
}
"""


class PromptTester:
    """Generates test cases and executes original and candidate prompts."""

    def __init__(self, backend: BaseLLMBackend):
        self.backend = backend

    def generate_test_cases(self, raw_prompt: str, analysis: AnalysisResult) -> List[TestCase]:
        """Synthesize test cases from task intent and requirements."""
        user_message = f"""<ORIGINAL_PROMPT>
{raw_prompt}
</ORIGINAL_PROMPT>

<TASK_INTENT>
{analysis.task_intent}
</TASK_INTENT>

<REQUIREMENTS>
{json.dumps([r.text for r in analysis.hard_requirements])}
</REQUIREMENTS>

Generate 2 distinct test scenarios in strict JSON.
"""
        response_text = self.backend.generate(
            prompt=user_message,
            system_instruction=TEST_GEN_SYSTEM_PROMPT,
            json_mode=True,
            temperature=0.2,
        )

        test_cases_raw = self._clean_and_parse_test_cases(response_text)
        return [TestCase.model_validate(tc) for tc in test_cases_raw]

    def execute_prompt(
        self,
        prompt_text: str,
        prompt_id: str,
        test_case: TestCase,
    ) -> ExecutionResult:
        """Execute a prompt against a test case and measure response latency."""
        full_execution_prompt = f"""{prompt_text}

---
[TEST INPUT SCENARIO]:
{test_case.input_scenario}
"""
        start_time = time.time()
        try:
            output = self.backend.generate(
                prompt=full_execution_prompt,
                temperature=0.2,
                max_tokens=1024,
            )
            latency_ms = (time.time() - start_time) * 1000.0
            return ExecutionResult(
                prompt_id=prompt_id,
                test_case_id=test_case.id,
                output_text=output,
                latency_ms=round(latency_ms, 2),
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000.0
            logger.error(f"Execution error for prompt {prompt_id} on {test_case.id}: {e}")
            return ExecutionResult(
                prompt_id=prompt_id,
                test_case_id=test_case.id,
                output_text="",
                latency_ms=round(latency_ms, 2),
                error=str(e),
            )

    def _clean_and_parse_test_cases(self, raw_str: str) -> List[Dict[str, Any]]:
        cleaned = raw_str.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        try:
            data = json.loads(cleaned)
            return data.get("test_cases", [])
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse test case JSON: {cleaned}")
            return [
                {
                    "id": "TC-01",
                    "name": "Default Test Scenario",
                    "input_scenario": "Sample data input",
                    "expected_behavior": "Executes core task correctly"
                }
            ]
