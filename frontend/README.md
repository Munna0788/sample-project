# Frontend Architecture: PromptCompiler UI & Visualizer

Welcome to the **Frontend Workspace** for the Agentic Prompt Optimization System.
This directory is designed for **Laptop 2 (Branch: `feature-frontend`)**.

## 📌 Architecture & Responsibilities

The frontend is an interactive developer dashboard that interfaces with the **PromptCompiler Backend API** (`http://localhost:8000`).

### Core Capabilities:
1. **Raw Prompt Ingestion**: Live character, word, and token estimation.
2. **Interactive Stepper Pipeline**: Visualizes stages in real-time:
   - 1. Semantic Analysis &rarr; 2. Transformation Planning &rarr; 3. Candidate Generation &rarr; 4. Test Execution &rarr; 5. Multi-Metric Evaluation &rarr; 6. Pareto Selection.
3. **Clarifications Modal**: Detects ambiguities from `/api/analyze` and queries user before compilation.
4. **Performance Metrics Dashboard**:
   - Token Savings Gauge (`%` reduction + delta)
   - Quality Score Gauge (`0.0 - 10.0` with baseline delta)
   - Invariants Retained (`100%` hard requirements preservation badge)
   - Redundancies Cut counter
5. **Output & Candidate Matrix**:
   - Side-by-side prompt diff
   - Multi-candidate ranking table (Concise vs Structured vs Operational)
   - Preserved invariants list & eliminated redundancies audit
   - Export options (Clipboard & JSON).

## 🚀 Running the Frontend

### Option 1: Served directly by FastAPI (Zero Setup)
When the backend runs (`python -m uvicorn prompt_optimizer.web.app:app --port 8000`), the dashboard is served automatically at:
```
http://localhost:8000/
```

### Option 2: Standalone Local Server (e.g. Live Server / Python http.server)
```bash
cd frontend
python -m http.server 3000
```
Open `http://localhost:3000` in your browser.

## 📡 API Contract (Backend Endpoints)
- `GET http://localhost:8000/api/health` &rarr; Check backend uptime
- `GET http://localhost:8000/api/backends` &rarr; List LLM backends (Ollama, Mock, OpenAI)
- `POST http://localhost:8000/api/analyze` &rarr; Run pre-scan for ambiguities & clarification questions
  - Body: `{"raw_prompt": "...", "backend_type": "ollama|mock|openai"}`
- `POST http://localhost:8000/api/optimize` &rarr; Run full compilation & return `FinalOptimizationReport`
  - Body: `{"raw_prompt": "...", "objective": "balanced|maximum_quality|maximum_compression", "backend_type": "..."}`
