# ⚡ PromptCompiler: Agentic Prompt Optimization System

> **The Prompt Compiler**: Natural language in &rarr; analyzed, planned, multi-candidate synthesized, simulated against generated test cases, evaluated with hard invariant preservation &rarr; Pareto-optimal, token-efficient prompt out.

---

## ⚡ Quickstart (1-Command Run)

### 🚀 Universal 1-Command Run (Windows PowerShell, CMD, macOS, Linux):
```bash
 run.bat
```

### 🪟 Windows (Batch script / Explorer):
```cmd
.\run.bat
```
*(Or simply double-click `run.bat` in Windows Explorer)*

### 🌐 Live Online Demo (No Installation Needed):
Open the live deployment directly in your browser:
**https://prompt-compiler.embarko.app**

### 🎯 What Happens Automatically:
1. Verifies and installs all dependencies (`requirements.txt`).
2. Starts the background FastAPI server on `http://localhost:8000`.
3. Launches the **Spotlight Desktop HUD** summoned with **`Win + O`** (or `Alt + O`).
4. Paste your raw prompt, press **`Enter`**, and instantly get the token-optimized prompt!

---

## 🎯 Architecture Overview

Unlike naive LLM prompt rewrites, **PromptCompiler** operates as a true compiler and optimization agent:
1. **Stage 1 (Semantic Decomposition)**: Extracts task intent, operational context, constraints, output schemas, explicit vs. implicit requirements, ambiguities, contradictions, and redundancies.
2. **Stage 2 (Invariant Separation)**: Strictly separates **Hard Requirements** (must *never* be dropped) from **Soft Preferences**.
3. **Stage 3 (Clarification Engine)**: Identifies missing critical parameters and formulates targeted clarification questions.
4. **Stage 4 (Optimization Planning)**: Produces an explainable blueprint detailing compression, removal, merging, and structural reorganization.
5. **Stage 5 (Multi-Candidate Generation)**: Generates 3 distinct prompt architectures:
   - `concise`: High compression, token-minimalist imperative directives.
   - `structured`: Hierarchical Markdown `# Role`, `# Objective`, `# Constraints`, `# Output Schema`.
   - `operational`: Explicit edge-case handling, resolved ambiguities, robust failure prevention.
6. **Stage 6 (Deterministic Token Measurement)**: Pure Python `tiktoken` deterministic measurement (tokens, characters, words, delta, % reduction).
7. **Stage 7 (Test Scenario Synthesis)**: Generates dynamic test inputs representing real-world caller payloads.
8. **Stage 8 (Simulation & LLM Execution)**: Runs baseline and all candidate prompts against generated test cases.
9. **Stage 9 (Multi-Dimensional Evaluation & Guardrails)**: Grades task correctness, requirement preservation, completeness, clarity, and schema adherence (0-10 scale). **Enforces strict safety guardrails: automatically rejects any candidate that drops a hard requirement or causes performance degradation.**
10. **Stage 10 (Iterative Refinement Loop)**: Diagnoses rejected candidates and executes self-healing prompt repair loops.
11. **Stage 11 (Multi-Objective Pareto Selection)**: Selects winning candidate based on configurable objective:
    - `maximum_quality`: Zero degradation, highest qualitative score.
    - `maximum_compression`: Maximum token reduction passing quality guardrails.
    - `balanced`: Pareto-optimal weighted balance (65% quality, 35% compression).
12. **Stage 12 (Comprehensive Audit Report)**: Detailed before/after tokens, quality delta, preserved invariants, eliminated redundancies, and selection rationale.

---

## 👥 Hackathon Team Division: Frontend vs. Backend

To enable seamless multi-laptop pair programming without merge conflicts, the system is strictly decoupled:

```
                               ┌─────────────────────────────┐
                               │   GitHub Shared Repo        │
                               │   Munna0788/sample-project  │
                               └──────────────┬──────────────┘
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      ▼                                               ▼
         ┌─────────────────────────┐                     ┌─────────────────────────┐
         │        Laptop 1         │                     │        Laptop 2         │
         │  Branch: feature-backend│                     │ Branch: feature-frontend│
         ├─────────────────────────┤                     ├─────────────────────────┤
         │ • Core Optimization    │                     │ • Interactive Dashboard │
         │   Pipeline (Core Agent) │                     │ • Stepper Visualizer    │
         │ • Tokenizer Engine      │                     │ • Live Token Gauge      │
         │ • Replaceable Backends  │                     │ • Clarifications Modal  │
         │ • Evaluator Guardrails  │                     │ • Side-by-side Diff     │
         │ • FastAPI Server        │                     │ • Candidate Matrix      │
         │ • Pytest Test Suite     │                     │ • JSON/Markdown Export  │
         └─────────────────────────┘                     └─────────────────────────┘
```

---

## 💻 Part 1: Backend Specification (Laptop 1)

### Directory: `prompt_optimizer/`
* `prompt_optimizer/models/`: Pydantic V2 data contracts (`AnalysisResult`, `OptimizationPlan`, `PromptCandidate`, `TestCase`, `CandidateEvaluation`, `FinalOptimizationReport`).
* `prompt_optimizer/backends/`:
  * `OllamaBackend`: Local Qwen2.5 / Llama execution via Ollama REST API.
  * `OpenAICompatibleBackend`: OpenAI, Gemini, Claude, Groq endpoint compatibility.
  * `MockLLMBackend`: Deterministic, ultra-fast simulation engine for testing and CI.
* `prompt_optimizer/core/`:
  * `tokenizer.py`: Deterministic token measurement with `tiktoken`.
  * `analyzer.py`: Semantic decomposition and invariant extractor.
  * `planner.py`: Transformation strategy planner.
  * `generator.py`: Multi-candidate synthesis (`concise`, `structured`, `operational`).
  * `tester.py`: Test case generator and runtime simulator.
  * `evaluator.py`: Multi-metric scoring and invariant guardrails.
  * `refiner.py`: Self-healing candidate refinement loop.
  * `selector.py`: Multi-objective Pareto ranker.
  * `optimizer.py`: Master orchestrator agent.
* `prompt_optimizer/web/app.py`: FastAPI server exposing:
  * `GET /api/health`
  * `GET /api/backends`
  * `POST /api/analyze`
  * `POST /api/optimize`
* `prompt_optimizer/cli/main.py`: Rich interactive terminal interface.

### Running Backend & Tests:
```bash
# Run test suite
pytest

# Run FastAPI server
python -m uvicorn prompt_optimizer.web.app:app --host 0.0.0.0 --port 8000 --reload

# Run CLI directly
python -m prompt_optimizer.cli.main optimize "Your raw prompt here" --backend mock --objective balanced
```

---

## 🎨 Part 2: Frontend Specification (Laptop 2)

### Directory: `frontend/`
* `frontend/index.html`: Responsive developer dashboard layout.
* `frontend/style.css`: Modern dark theme (Cursor/Linear aesthetic, JetBrains Mono typography).
* `frontend/app.js`: Reactive UI logic interfacing with backend API.

### Core Frontend Components:
1. **Raw Prompt Input Area**: Textarea with live character/word/token counter.
2. **Objective Controls**:
   - `Balanced (Pareto)`: Default optimal trade-off.
   - `Maximum Quality`: Strict zero-degradation mode.
   - `Maximum Compression`: Aggressive token pruning.
3. **Engine Selector**: Switch between Local Ollama, Mock Engine, or Cloud APIs.
4. **Pipeline Stepper**: Animated stage visualizer tracking compiler progress.
5. **Interactive Clarifications Modal**: Pops up when ambiguities or missing parameters are detected.
6. **Key Metrics Display**:
   - Token Savings (`-%` reduction, delta).
   - Quality Score (`0.0 - 10.0` with baseline delta).
   - Invariants Retained (`100%` fidelity badge).
   - Redundancies Cut counter.
7. **Side-by-side Prompt Diff**: Original vs Compiled with one-click copy.
8. **Candidate Comparison Matrix**: Real-time table ranking all 3 candidate architectures.
9. **Audit JSON Inspector**: Complete audit trail for debugging and export.

### Running the Frontend:
```bash
cd frontend
python -m http.server 3000
```
Open `http://localhost:3000` (or access via FastAPI on `http://localhost:8000`).

---

## 🔄 Git Collaboration Workflow for Both Laptops

### 1. Laptop 1 (Backend Engineer):
```bash
git checkout -b feature-backend
git add .
git commit -m "feat(backend): complete agentic prompt compiler pipeline and API"
git push origin feature-backend
```

### 2. Laptop 2 (Frontend Engineer):
```bash
git clone https://github.com/Munna0788/sample-project.git
cd sample-project
git checkout -b feature-frontend
# Work on files inside frontend/
git add frontend/
git commit -m "feat(frontend): enhance interactive visualizer and candidate comparison"
git push origin feature-frontend
```

### 3. Merging:
Both branches can be reviewed and merged into `main` via GitHub PR or direct merge with zero conflicts.
