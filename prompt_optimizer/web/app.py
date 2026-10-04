"""FastAPI Backend Server for Prompt Compiler."""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from prompt_optimizer.models.analysis import AnalysisResult
from prompt_optimizer.models.report import FinalOptimizationReport, OptimizationObjective
from prompt_optimizer.backends.ollama import OllamaBackend
from prompt_optimizer.backends.openai_compat import OpenAICompatibleBackend
from prompt_optimizer.backends.mock import MockLLMBackend
from prompt_optimizer.backends.base import BaseLLMBackend
from prompt_optimizer.core.optimizer import PromptOptimizerAgent

app = FastAPI(
    title="Agentic Prompt Optimization System API",
    description="Backend compiler and optimization engine for LLM prompts.",
    version="1.0.0",
)

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
    backend_type: str = Field(default="ollama", description="ollama | openai | mock")
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
    return {
        "backends": [
            {
                "id": "ollama",
                "name": "Local Ollama",
                "available": ollama.is_available(),
                "default_model": ollama.model,
            },
            {
                "id": "openai",
                "name": "OpenAI / Claude / Gemini Compatible API",
                "available": openai.is_available(),
                "default_model": openai.model,
            },
            {
                "id": "mock",
                "name": "Deterministic Mock (Fast Simulation)",
                "available": True,
                "default_model": "mock-agentic-v1",
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
    """Run full optimization pipeline and return the final report."""
    backend = get_backend(req.backend_type, req.model_name)
    agent = PromptOptimizerAgent(backend=backend)
    try:
        report = agent.optimize(
            raw_prompt=req.raw_prompt,
            objective=req.objective,
            clarification_answers=req.clarification_answers,
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


# Serve static frontend dashboard if static directory exists
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
