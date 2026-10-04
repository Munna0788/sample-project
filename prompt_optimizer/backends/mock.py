"""Dynamic Context-Aware Mock LLM Backend for lightning-fast testing, simulation, and offline hackathon demos.
Extracts semantic intent, domain roles, and invariants dynamically from the user's prompt so outputs are tailored every time.
"""

import json
import re
from typing import Optional, Dict, Any, List

from prompt_optimizer.backends.base import BaseLLMBackend


def _extract_raw_prompt(text: str) -> str:
    """Extract raw prompt payload from various stage envelopes."""
    m = re.search(r"<ORIGINAL_PROMPT>(.*?)</ORIGINAL_PROMPT>", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    m2 = re.search(r"<PROMPT>(.*?)</PROMPT>", text, re.DOTALL)
    if m2:
        return m2.group(1).strip()
    m3 = re.search(r"Analyze the following prompt:\s*\n*(.*?)(?:\n\s*Respond with|\Z)", text, re.DOTALL | re.IGNORECASE)
    if m3:
        return m3.group(1).strip()
    clean = re.sub(r"<[^>]+>", "", text).strip()
    return clean[:500] if clean else "Perform task according to specifications"


def _analyze_text(raw_text: str) -> Dict[str, Any]:
    """Dynamically extract semantic properties, domain roles, and invariants from input text."""
    lower = raw_text.lower()

    # Clean conversational fluff and politeness markers
    cleaned = re.sub(
        r"^(hey|hello|hi|good morning|dear assistant|please|could you please|can you please|would you please|i need you to|kindly)\s*[,!:]*\s*",
        "", raw_text, flags=re.IGNORECASE
    ).strip()
    cleaned = re.sub(
        r"(please\s+remember\s+to|as\s+i\s+said\s+before|thank\s+you\s*!*|thanks\s*!*|cheers\s*!*)\.?\s*$",
        "", cleaned, flags=re.IGNORECASE
    ).strip()
    if not cleaned:
        cleaned = raw_text.strip()

    # Domain role detection
    role = "Domain Subject Specialist"
    if any(k in lower for k in ["python", "script", "function", "django", "fastapi", "flask", "async", "pandas"]):
        role = "Senior Python Software Architect"
    elif any(k in lower for k in ["sql", "postgres", "mysql", "database", "query", "schema", "table"]):
        role = "Principal Database & SQL Engineer"
    elif any(k in lower for k in ["csv", "json", "extract", "parse", "scrape", "data", "scraper"]):
        role = "Senior Data Processing & Web Extraction Engineer"
    elif any(k in lower for k in ["support", "customer", "refund", "ticket", "polite", "client"]):
        role = "Customer Success & Communications Specialist"
    elif any(k in lower for k in ["security", "audit", "vulnerability", "leak", "injection", "auth"]):
        role = "Application Security & Code Auditor"
    elif any(k in lower for k in ["docker", "k8s", "kubernetes", "aws", "deploy", "server", "linux", "cloud"]):
        role = "DevOps & Cloud Infrastructure Engineer"
    elif any(k in lower for k in ["review", "refactor", "code review", "smell", "clean code"]):
        role = "Lead Software Reviewer & Code Quality Specialist"
    elif any(k in lower for k in ["write", "article", "blog", "essay", "content", "summary"]):
        role = "Professional Technical Communications Specialist"
    elif any(k in lower for k in ["math", "calculate", "statistics", "average", "metric", "cpu", "memory"]):
        role = "Systems Performance & Quantitative Analyst"

    # Invariants extraction
    hard_invariants: List[str] = []

    # 1. Output format invariants
    if "json" in lower:
        hard_invariants.append("Strict Output Format: Output must be strictly valid JSON without external markdown fences or conversational pre/post-text.")
    elif "csv" in lower:
        hard_invariants.append("Format Invariant: Structure output as clean, RFC 4180-compliant CSV records.")
    elif "table" in lower or "markdown" in lower:
        hard_invariants.append("Format Invariant: Render outputs in a structured Markdown table format.")

    # 2. Negative constraints (from prompt)
    negatives = re.findall(r"(?:never|do not|don't|must not|avoid|strictly\s+no)\s+[^.,;\n]+", raw_text, re.IGNORECASE)
    for neg in negatives:
        s = neg.strip().capitalize()
        if not s.endswith("."):
            s += "."
        if s not in hard_invariants:
            hard_invariants.append(s)

    # 3. Default guards if none found
    if not any("hallucinat" in h.lower() or "fabricat" in h.lower() for h in hard_invariants):
        hard_invariants.append("Invariant: Never fabricate, invent, or hallucinate omitted parameters or unverified facts.")
    if len(hard_invariants) < 2:
        hard_invariants.append("Error Handling: Handle boundary edge cases and invalid inputs gracefully without fatal failures.")

    # Extract sentence-level compressed task
    sentences = re.split(r"[.!?\n]+", raw_text)
    task_sentences = []
    for s in sentences:
        s_clean = s.strip()
        s_lower = s_clean.lower()
        if not s_clean:
            continue
        if any(fluff in s_lower for fluff in [
            "do this task for me", "great care and attention", "make sure that you do not forget",
            "telling you right now", "thank you", "thanks so much", "i would appreciate", "kindly do this"
        ]):
            continue
        s_clean = re.sub(r"^(please|could you kindly|kindly|can you|would you|hello|hey|hi)\s*", "", s_clean, flags=re.IGNORECASE).strip()
        if s_clean and len(s_clean) > 8:
            task_sentences.append(s_clean)

    compressed_task = ". ".join(task_sentences).strip()
    if not compressed_task:
        compressed_task = cleaned
    if not compressed_task.endswith("."):
        compressed_task += "."

    # Ambiguity detection: Only trigger when prompt has vague markers or lacks essential specs
    words = raw_text.split()
    vague_markers = [
        "something", "cool", "stuff", "short and cool", "vague", "some code",
        "make me something", "do something", "create something", "write something",
        "some app", "some script", "whatever you want"
    ]
    has_vague_words = any(w in lower for w in vague_markers)
    missing_scrape_target = ("scrape" in lower or "crawler" in lower) and not any(k in lower for k in ["http", "url", "site", "web", "html", "article", "page", "domain", "data", "records", "csv"])
    too_short_and_generic = len(words) < 5 and not any(k in lower for k in ["python", "json", "csv", "sql", "email", "bug", "fix", "function", "script", "review", "test"])

    is_ambiguous = has_vague_words or missing_scrape_target or too_short_and_generic
    ambiguities = []
    clarification_questions = []

    if is_ambiguous:
        ambiguities.append({
            "id": "AMB-01",
            "description": "Output schema or delivery format is underspecified in the prompt.",
            "possible_interpretations": ["Structured JSON", "Markdown Table", "Plain text bullet list"],
            "suggested_resolution": "Specify the exact desired return format."
        })
        clarification_questions.append({
            "id": "CLAR-01",
            "question": f"What specific output format or schema should the {role} generate?",
            "reason": "Unspecified format causes output variance across executions.",
            "default_assumption": "Strict JSON output",
            "suggested_options": ["Strict JSON", "Markdown Table", "Plain text bullets"]
        })

    return {
        "role": role,
        "cleaned_task": cleaned,
        "compressed_task": compressed_task,
        "hard_invariants": hard_invariants,
        "is_ambiguous": is_ambiguous,
        "ambiguities": ambiguities,
        "clarification_questions": clarification_questions,
        "has_json": "json" in lower
    }


def _build_high_precision_prompt(analysis: Dict[str, Any], raw_text: str) -> str:
    """Build a tailored, structured High Precision prompt."""
    role = analysis["role"]
    task = analysis["cleaned_task"]
    invariants = analysis["hard_invariants"]

    hp = f"# Role & Persona\nYou are an expert {role}.\n\n"
    hp += f"# Objective & Scope\n{task}\n\n"
    hp += "# Strict Execution Invariants\n"
    for i, inv in enumerate(invariants, 1):
        hp += f"{i}. {inv}\n"

    hp += "\n# Edge Cases & Guardrails\n"
    hp += "- Input Validation: Verify inputs prior to execution; do not assume omitted parameters.\n"
    hp += "- Determinism: Enforce 100% adherence to invariants above with zero conversational commentary.\n"

    if analysis.get("has_json"):
        hp += "\n# Output Schema\n```json\n{\n  \"status\": \"success\",\n  \"data\": {}\n}\n```\nOutput ONLY valid raw JSON."
    else:
        hp += "\n# Output Format\nProvide the complete solution structured in clean Markdown with clear code blocks or bullet points as appropriate."

    return hp


def _build_concise_prompt(analysis: Dict[str, Any], raw_text: str) -> str:
    """Build a dense, token-minimalist Concise prompt."""
    task = analysis.get("compressed_task", analysis["cleaned_task"])
    inv = analysis["hard_invariants"][0] if analysis["hard_invariants"] else "Do not hallucinate."
    return f"{task}\n- Rule: {inv}\n- Be concise."


class MockLLMBackend(BaseLLMBackend):
    """Dynamic, Context-Aware Mock LLM Backend that tailors every output to the user's prompt."""

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
        sys_str = (system_instruction or "").lower()
        lower_prompt = prompt.lower()
        raw_prompt = _extract_raw_prompt(prompt)
        analysis = _analyze_text(raw_prompt)

        # Quick Box Dual Synthesis Prompt
        if "dual-result" in sys_str or "dual synthesis" in sys_str or "synthesize both" in lower_prompt:
            concise = _build_concise_prompt(analysis, raw_prompt)
            high_prec = _build_high_precision_prompt(analysis, raw_prompt)
            return json.dumps({
                "concise_prompt": concise,
                "concise_rationale": "High token compression removing conversational filler and structuring requirements as direct imperatives.",
                "high_precision_prompt": high_prec,
                "high_precision_rationale": f"Explicit role definition ({analysis['role']}), structured sections, and enforced invariants."
            })

        # Stage 2: Planning Prompt
        if "planner" in sys_str or "optimization plan" in lower_prompt:
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
                "reorganization_strategy": f"Adopt standard Agent Protocol for {analysis['role']}: Role -> Objective -> Invariants -> Output Format",
                "hard_requirement_invariants": [
                    f"REQ-01: {inv}" for inv in analysis["hard_invariants"][:2]
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
                "plan_rationale": f"Refactor into dense imperative structure preserving all hard constraints for {analysis['role']}."
            })

        # Stage 3: Candidate Generation Prompt
        if "candidate generator" in sys_str or "candidate" in lower_prompt:
            concise_text = _build_concise_prompt(analysis, raw_prompt)
            hp_text = _build_high_precision_prompt(analysis, raw_prompt)
            return json.dumps({
                "candidates": [
                    {
                        "id": "cand_concise",
                        "strategy": "concise",
                        "prompt_text": concise_text,
                        "rationale": "High token compression removing conversational filler and structuring requirements as direct imperatives.",
                        "preserved_hard_requirements": ["REQ-01", "REQ-02"],
                        "changes_summary": ["Removed conversational boilerplate", "Compressed rules into bullet points"]
                    },
                    {
                        "id": "cand_structured",
                        "strategy": "structured",
                        "prompt_text": hp_text,
                        "rationale": "Hierarchical Markdown architecture optimizing prompt comprehension and structural adherence.",
                        "preserved_hard_requirements": ["REQ-01", "REQ-02"],
                        "changes_summary": ["Organized into clear sections", "Included explicit schema delimiter"]
                    },
                    {
                        "id": "cand_operational",
                        "strategy": "operational",
                        "prompt_text": f"You are an automated {analysis['role']}.\nTask: {analysis['cleaned_task']}\nRules:\n1. {analysis['hard_invariants'][0]}\n2. Fail gracefully on missing arguments.",
                        "rationale": "Operational framing clarifying edge cases and strict execution invariants.",
                        "preserved_hard_requirements": ["REQ-01", "REQ-02"],
                        "changes_summary": ["Explicit edge case handling", "Reinforced strict output invariant"]
                    }
                ]
            })

        # Stage 4: Test Case Generation
        if "test suite generator" in sys_str or "generate 2 distinct test scenarios" in lower_prompt:
            return json.dumps({
                "test_cases": [
                    {
                        "id": "TC-01",
                        "name": f"Standard {analysis['role']} Execution",
                        "input_scenario": f"Valid standard execution scenario for: {analysis['cleaned_task'][:50]}",
                        "expected_behavior": "Executes task adhering completely to all specified invariants."
                    },
                    {
                        "id": "TC-02",
                        "name": "Edge Case & Boundary Scenario",
                        "input_scenario": "Invalid or incomplete inputs provided.",
                        "expected_behavior": "Handles edge case gracefully without hallucinating unverified outputs."
                    }
                ]
            })

        # Stage 5: Evaluation Prompt
        if "evaluator" in sys_str or "grade output adherence" in lower_prompt or "evaluat" in lower_prompt:
            return json.dumps({
                "task_correctness": 9.6,
                "requirement_preservation": 9.9,
                "completeness": 9.5,
                "clarity": 9.7,
                "output_format_adherence": 10.0,
                "overall_quality_score": 9.7,
                "satisfied_hard_requirements": ["REQ-01", "REQ-02"],
                "violated_hard_requirements": [],
                "evaluation_notes": f"Prompt produced compliant, high-precision output for {analysis['role']} with zero invariant violations."
            })

        # Stage 6: Refinement Specialist Prompt
        if "refinement specialist" in sys_str or "healed and refined prompt" in lower_prompt:
            return json.dumps({
                "refined_prompt": _build_high_precision_prompt(analysis, raw_prompt),
                "rationale": "Restored required invariants and eliminated formatting deviations.",
                "fixed_issues": ["Restored missing hard requirements"]
            })

        # Stage 1: Analysis Prompt
        if "analyzer" in sys_str or "analyze the following prompt" in lower_prompt:
            return json.dumps({
                "task_intent": analysis["cleaned_task"],
                "context": f"Execution context for {analysis['role']}",
                "constraints": analysis["hard_invariants"],
                "desired_output": "Structured output complying strictly with specified invariants",
                "tone_style": "Clear, concise, professional technical tone",
                "explicit_requirements": [analysis["cleaned_task"]] + analysis["hard_invariants"][:2],
                "implicit_requirements": [
                    "Handle empty or invalid inputs gracefully",
                    "Deterministic format adherence"
                ],
                "hard_requirements": [
                    {
                        "id": f"REQ-0{i}",
                        "text": inv,
                        "type": "hard",
                        "category": "functional" if i == 2 else "format",
                        "source_phrase": inv[:30]
                    }
                    for i, inv in enumerate(analysis["hard_invariants"][:3], 1)
                ],
                "soft_preferences": [
                    {
                        "id": "PREF-01",
                        "text": "Professional and courteous phrasing",
                        "type": "soft",
                        "category": "style",
                        "source_phrase": "polite"
                    }
                ],
                "ambiguities": analysis["ambiguities"],
                "contradictions": [],
                "redundant_instructions": [
                    {
                        "id": "RED-01",
                        "phrase": "Please please make sure to always remember",
                        "reason": "Conversational fluff repeating instruction"
                    }
                ],
                "missing_critical_info": [],
                "clarification_questions": analysis["clarification_questions"]
            })

        # Default fallback
        if json_mode:
            return json.dumps({"status": "success", "content": f"Processed prompt for {analysis['role']}."})
        return f"Deterministic output generated for {analysis['role']}: {analysis['cleaned_task']}"
