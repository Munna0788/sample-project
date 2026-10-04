# Frontend Architecture: PromptCompiler UI & Visualizer

Welcome to the **Frontend Workspace** for the Agentic Prompt Optimization System.
This directory is designed for **Laptop 2 (Branch: `feature-frontend`)**.

## 📌 Architecture & Responsibilities

The frontend is an interactive developer dashboard that interfaces with the **PromptCompiler Backend API** (`http://localhost:8000` or configurable remote IP).

### Core Capabilities:
1. **Raw Prompt Ingestion & Presets**:
   - Live character, word, and token estimation (calibrated against `tiktoken`).
   - One-click demo presets (*CSV Analyst*, *Support Bot*, *JSON Extractor*, *Code Reviewer*).
   - Clear and clipboard paste utilities with keyboard shortcut (`Ctrl+Enter` / `Cmd+Enter`).
2. **Interactive Stepper Pipeline**: Visualizes stages in real-time:
   - 1. Semantic Analysis &rarr; 2. Transformation Planning &rarr; 3. Candidate Generation &rarr; 4. Test Simulation &rarr; 5. Multi-Metric Evaluation &rarr; 6. Pareto Selection.
3. **Targeted Clarifications Modal**: Detects ambiguities from `/api/analyze` and queries user before compilation.
4. **Performance Metrics & ROI Calculator**:
   - Token Savings Gauge (`%` reduction + delta + progress bar).
   - Quality Score Gauge (`0.0 - 10.0` with baseline delta).
   - Invariants Retained (`100%` hard requirements preservation badge).
   - Redundancies Cut counter.
   - **Financial Savings (ROI) Calculator**: Live annual cost reduction projections across GPT-4o, Claude 3.5 Sonnet, and Gemini 1.5 Pro based on configurable monthly volume (100k - 20M calls).
5. **Multi-Mode Visual Diff & Syntax Highlighting Engine**:
   - **↔️ Side-by-Side Visual Diff**: Word-level LCS (Longest Common Subsequence) diff highlighting eliminated redundancies in red strikethrough and added directives in green.
   - **✨ Highlighted Output**: Syntax highlighting for Markdown headings (`# Role`, `# Constraints`), bullet points, directive keywords (`MUST`, `NEVER`, `ALWAYS`), and variables (`{var}`).
   - **↕️ Unified Diff**: Line-by-line git-style diff view.
   - **📄 Raw Text**: Clean preformatted text view with one-click copy and JSON export.
6. **Interactive Candidate Matrix & Deep Dive**:
   - Multi-candidate ranking table (Concise vs Structured vs Operational).
   - Expandable candidate drawer displaying 5-dimensional score bars (Task Correctness, Requirement Preservation, Completeness, Clarity, Schema Adherence).
   - Evaluator qualitative feedback and simulated test case execution traces with latency measurements.
7. **Audit & Traceability**:
   - Preserved invariants catalog with category badges.
   - Eliminated redundancies catalog.
   - Syntax-colored machine-readable `FinalOptimizationReport` JSON viewer.
8. **Configurable Backend Host**:
   - Seamlessly connect to Laptop 1 via local network IP (e.g. `http://192.168.1.50:8000`) with persistent storage and live connection status ping.

---

## 🚀 Running the Frontend

### Option 1: Standalone Local Server (e.g. Python http.server)
```bash
cd frontend
python3 -m http.server 3000
```
Open `http://localhost:3000` in your browser. (The dashboard will automatically connect to `http://localhost:8000` for API calls).

### Option 2: Served directly by FastAPI (Zero Setup)
When the backend runs on Laptop 1 (`python -m uvicorn prompt_optimizer.web.app:app --host 0.0.0.0 --port 8000`), the dashboard is served automatically at:
```
http://localhost:8000/
```

---

## 📡 API Contract (Backend Endpoints)
- `GET http://localhost:8000/api/health` &rarr; Check backend uptime
- `GET http://localhost:8000/api/backends` &rarr; List LLM backends (Ollama, Mock, OpenAI)
- `POST http://localhost:8000/api/analyze` &rarr; Run pre-scan for ambiguities & clarification questions
  - Body: `{"raw_prompt": "...", "backend_type": "ollama|mock|openai"}`
- `POST http://localhost:8000/api/optimize` &rarr; Run full compilation & return `FinalOptimizationReport`
  - Body: `{"raw_prompt": "...", "objective": "balanced|maximum_quality|maximum_compression", "backend_type": "..."}`
