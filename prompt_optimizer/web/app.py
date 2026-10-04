"""FastAPI Backend Server for Prompt Compiler."""

import json
import os
import queue
import threading
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from prompt_optimizer.models.analysis import AnalysisResult
from prompt_optimizer.models.report import FinalOptimizationReport, OptimizationObjective
from prompt_optimizer.backends.ollama import OllamaBackend
from prompt_optimizer.backends.openai_compat import OpenAICompatibleBackend
from prompt_optimizer.backends.gemini import GeminiBackend
from prompt_optimizer.backends.mock import MockLLMBackend
from prompt_optimizer.backends.base import BaseLLMBackend
from prompt_optimizer.core.optimizer import PromptOptimizerAgent
from prompt_optimizer.storage.history import HistoryStore, RunSummary
from prompt_optimizer.benchmarks.suite import BenchmarkSuite, BenchmarkReport

app = FastAPI(
    title="Agentic Prompt Optimization System API",
    description="Compiler, verification engine, and optimization agent for LLM prompts.",
    version="1.0.0",
)

history_store = HistoryStore()

# Enable CORS for cross-laptop frontend-backend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OptimizeRequest(BaseModel):
    raw_prompt: str = Field(..., min_length=3, description="Raw, unoptimized prompt text")
    objective: OptimizationObjective = Field(
        default=OptimizationObjective.BALANCED,
        description="maximum_quality | maximum_compression | balanced"
    )
    backend_type: str = Field(default="ollama", description="ollama | openai | gemini | mock")
    model_name: Optional[str] = Field(default=None, description="Model identifier")
    clarification_answers: Optional[Dict[str, str]] = Field(
        default=None,
        description="Map of question IDs to user answers"
    )


class AnalyzeRequest(BaseModel):
    raw_prompt: str = Field(..., min_length=3)
    backend_type: str = Field(default="ollama")
    model_name: Optional[str] = Field(default=None)


def get_backend(b_type: str, model_name: Optional[str]) -> BaseLLMBackend:
    b_type_lower = b_type.lower()
    if b_type_lower == "ollama":
        model = model_name or "goekdenizguelmez/JOSIEFIED-Qwen2.5:7b"
        backend = OllamaBackend(model=model)
        if not backend.is_available():
            return MockLLMBackend()
        return backend
    elif b_type_lower == "gemini":
        return GeminiBackend(model=model_name or "gemini-1.5-flash")
    elif b_type_lower == "openai":
        return OpenAICompatibleBackend(model=model_name or "gpt-4o-mini")
    else:
        return MockLLMBackend(model=model_name or "mock-agentic-v1")


@app.get("/api/health")
def health_check():
    """Health check endpoint for frontend and monitoring."""
    return {"status": "ok", "service": "prompt-compiler-backend"}


@app.get("/api/backends")
def list_backends():
    """Returns status and availability of configured backends."""
    ollama = OllamaBackend()
    openai = OpenAICompatibleBackend()
    gemini = GeminiBackend()
    return {
        "backends": [
            {
                "id": "ollama",
                "name": "Local Ollama",
                "available": ollama.is_available(),
                "default_model": ollama.model,
            },
            {
                "id": "mock",
                "name": "Deterministic Mock (Fast Simulation)",
                "available": True,
                "default_model": "mock-agentic-v1",
            },
            {
                "id": "gemini",
                "name": "Google Gemini API",
                "available": gemini.is_available(),
                "default_model": gemini.model,
            },
            {
                "id": "openai",
                "name": "OpenAI / Claude / Compatible API",
                "available": openai.is_available(),
                "default_model": openai.model,
            },
        ]
    }


@app.post("/api/analyze", response_model=AnalysisResult)
def analyze_prompt(req: AnalyzeRequest):
    """Analyze a raw prompt to extract semantics, invariants, and ambiguities."""
    backend = get_backend(req.backend_type, req.model_name)
    agent = PromptOptimizerAgent(backend=backend)
    try:
        return agent.analyzer.analyze(req.raw_prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/optimize", response_model=FinalOptimizationReport)
def optimize_prompt(req: OptimizeRequest):
    """Run full optimization pipeline, store audit trail, and return final report."""
    backend = get_backend(req.backend_type, req.model_name)
    agent = PromptOptimizerAgent(backend=backend)
    try:
        report = agent.optimize(
            raw_prompt=req.raw_prompt,
            objective=req.objective,
            clarification_answers=req.clarification_answers,
        )
        # Persist run to SQLite history
        history_store.save_run(report)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@app.post("/api/optimize/stream")
def optimize_prompt_stream(req: OptimizeRequest):
    """Stream compiler execution stages and real-time events via Server-Sent Events (SSE)."""
    event_queue: queue.Queue = queue.Queue()

    def progress_callback(stage: str, details: Dict[str, Any]):
        event_queue.put({"stage": stage, "details": details})

    def run_worker():
        backend = get_backend(req.backend_type, req.model_name)
        agent = PromptOptimizerAgent(backend=backend)
        try:
            report = agent.optimize(
                raw_prompt=req.raw_prompt,
                objective=req.objective,
                clarification_answers=req.clarification_answers,
                progress_callback=progress_callback,
            )
            history_store.save_run(report)
            event_queue.put({"stage": "DONE", "report": report.model_dump()})
        except Exception as e:
            event_queue.put({"stage": "ERROR", "error": str(e)})
        finally:
            event_queue.put(None)  # Sentinel to end stream

    worker_thread = threading.Thread(target=run_worker)
    worker_thread.start()

    def event_generator():
        while True:
            item = event_queue.get()
            if item is None:
                break
            payload = json.dumps(item)
            yield f"data: {payload}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/history", response_model=List[RunSummary])
def list_history(limit: int = 30):
    """Retrieve historical optimization runs."""
    return history_store.list_runs(limit=limit)


@app.get("/api/history/{run_id}", response_model=FinalOptimizationReport)
def get_historical_run(run_id: str):
    """Retrieve complete audit report for a specific run ID."""
    report = history_store.get_run(run_id)
    if not report:
        raise HTTPException(status_code=404, detail="Run not found.")
    return report


@app.post("/api/benchmarks/run", response_model=BenchmarkReport)
def run_benchmarks(backend_type: str = "mock"):
    """Execute benchmark suite against the chosen backend."""
    backend = get_backend(backend_type, None)
    agent = PromptOptimizerAgent(backend=backend)
    suite = BenchmarkSuite(agent=agent)
    return suite.run_all()


# Mount static web dashboard
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
