"""Tests for SQLite history storage."""

import pytest
from pathlib import Path
from prompt_optimizer.storage.history import HistoryStore
from prompt_optimizer.models.report import FinalOptimizationReport, OptimizationObjective


def test_history_store_save_and_retrieve(tmp_path):
    db_file = tmp_path / "test_history.db"
    store = HistoryStore(db_path=db_file)

    report = FinalOptimizationReport(
        original_prompt="Verbose test prompt for history",
        final_optimized_prompt="Clean prompt",
        original_tokens=30,
        final_tokens=15,
        tokens_saved=15,
        percentage_reduction=50.0,
        original_quality_score=8.0,
        final_quality_score=9.0,
        quality_delta=1.0,
        preserved_hard_requirements=["REQ-01: Accuracy"],
        preserved_soft_preferences=[],
        removed_redundancies=[],
        detected_ambiguities=[],
        optimization_iterations=1,
        selection_objective=OptimizationObjective.BALANCED,
        selected_candidate_id="cand_concise",
        selection_rationale="Fast and precise",
    )

    run_id = store.save_run(report)
    assert run_id.startswith("opt_")

    runs = store.list_runs()
    assert len(runs) == 1
    assert runs[0].run_id == run_id
    assert runs[0].tokens_saved == 15
    assert runs[0].percentage_reduction == 50.0

    retrieved = store.get_run(run_id)
    assert retrieved is not None
    assert retrieved.original_prompt == "Verbose test prompt for history"
    assert retrieved.final_optimized_prompt == "Clean prompt"
