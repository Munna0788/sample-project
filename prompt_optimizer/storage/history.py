"""Persistent storage and audit history for prompt optimization runs."""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from prompt_optimizer.models.report import FinalOptimizationReport, OptimizationObjective

DB_PATH = Path(__file__).resolve().parent / "optimization_history.db"


class RunSummary(BaseModel):
    """Compact summary of a historical optimization run."""
    run_id: str
    timestamp: str
    original_prompt_preview: str
    selected_candidate_id: str
    selection_objective: str
    original_tokens: int
    final_tokens: int
    tokens_saved: int
    percentage_reduction: float
    final_quality_score: float
    quality_delta: float


class HistoryStore:
    """SQLite-backed audit trail for optimization runs."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS optimization_runs (
                    run_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    original_prompt TEXT NOT NULL,
                    selected_candidate_id TEXT NOT NULL,
                    selection_objective TEXT NOT NULL,
                    original_tokens INTEGER NOT NULL,
                    final_tokens INTEGER NOT NULL,
                    tokens_saved INTEGER NOT NULL,
                    percentage_reduction REAL NOT NULL,
                    final_quality_score REAL NOT NULL,
                    quality_delta REAL NOT NULL,
                    report_json TEXT NOT NULL
                )
            """)
            conn.commit()

    def save_run(self, report: FinalOptimizationReport) -> str:
        """Store a completed optimization run."""
        run_id = f"opt_{uuid.uuid4().hex[:10]}"
        timestamp = datetime.now(timezone.utc).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO optimization_runs (
                    run_id, timestamp, original_prompt, selected_candidate_id,
                    selection_objective, original_tokens, final_tokens,
                    tokens_saved, percentage_reduction, final_quality_score,
                    quality_delta, report_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                timestamp,
                report.original_prompt,
                report.selected_candidate_id,
                report.selection_objective.value,
                report.original_tokens,
                report.final_tokens,
                report.tokens_saved,
                report.percentage_reduction,
                report.final_quality_score,
                report.quality_delta,
                report.model_dump_json(),
            ))
            conn.commit()
        return run_id

    def list_runs(self, limit: int = 50) -> List[RunSummary]:
        """List past optimization runs ordered by newest first."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    run_id, timestamp, original_prompt, selected_candidate_id,
                    selection_objective, original_tokens, final_tokens,
                    tokens_saved, percentage_reduction, final_quality_score,
                    quality_delta
                FROM optimization_runs
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()

        summaries = []
        for r in rows:
            prompt_preview = r[2][:80] + "..." if len(r[2]) > 80 else r[2]
            summaries.append(RunSummary(
                run_id=r[0],
                timestamp=r[1],
                original_prompt_preview=prompt_preview,
                selected_candidate_id=r[3],
                selection_objective=r[4],
                original_tokens=r[5],
                final_tokens=r[6],
                tokens_saved=r[7],
                percentage_reduction=r[8],
                final_quality_score=r[9],
                quality_delta=r[10],
            ))
        return summaries

    def get_run(self, run_id: str) -> Optional[FinalOptimizationReport]:
        """Retrieve full audit report for a specific run."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT report_json FROM optimization_runs WHERE run_id = ?", (run_id,))
            row = cursor.fetchone()
            if not row:
                return None
            data = json.loads(row[0])
            return FinalOptimizationReport.model_validate(data)
