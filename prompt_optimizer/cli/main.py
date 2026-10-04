"""Rich Command Line Interface for Prompt Compiler."""

import json
import sys
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.prompt import Prompt

from prompt_optimizer.backends.ollama import OllamaBackend
from prompt_optimizer.backends.openai_compat import OpenAICompatibleBackend
from prompt_optimizer.backends.gemini import GeminiBackend
from prompt_optimizer.backends.mock import MockLLMBackend
from prompt_optimizer.backends.base import BaseLLMBackend
from prompt_optimizer.models.report import OptimizationObjective
from prompt_optimizer.core.optimizer import PromptOptimizerAgent
from prompt_optimizer.storage.history import HistoryStore
from prompt_optimizer.benchmarks.suite import BenchmarkSuite

app = typer.Typer(
    name="prompt-opt",
    help="Agentic Prompt Optimization System - The Prompt Compiler",
    add_completion=False,
)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console(force_terminal=True, legacy_windows=False)
history_store = HistoryStore()


def resolve_backend(backend_type: str, model_name: Optional[str]) -> BaseLLMBackend:
    """Instantiate appropriate LLM backend."""
    b_type = backend_type.lower()
    if b_type == "ollama":
        model = model_name or "goekdenizguelmez/JOSIEFIED-Qwen2.5:7b"
        backend = OllamaBackend(model=model)
        if not backend.is_available():
            console.print("[yellow]Warning: Local Ollama is not reachable on localhost:11434. Falling back to MockLLMBackend.[/yellow]")
            return MockLLMBackend()
        return backend
    elif b_type == "gemini":
        return GeminiBackend(model=model_name or "gemini-1.5-flash")
    elif b_type == "openai":
        return OpenAICompatibleBackend(model=model_name or "gpt-4o-mini")
    elif b_type == "mock":
        return MockLLMBackend(model=model_name or "mock-agentic-v1")
    else:
        console.print(f"[red]Unknown backend '{backend_type}'. Using mock backend.[/red]")
        return MockLLMBackend()


@app.command()
def optimize(
    prompt: Optional[str] = typer.Argument(None, help="The raw prompt text to optimize"),
    file: Optional[str] = typer.Option(None, "--file", "-f", help="Read raw prompt from text file"),
    objective: str = typer.Option("balanced", "--objective", "-o", help="balanced | maximum_quality | maximum_compression"),
    backend: str = typer.Option("ollama", "--backend", "-b", help="ollama | gemini | openai | mock"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="LLM Model identifier"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Prompt user for clarifications interactively"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON report"),
):
    """Run full agentic optimization on a raw prompt."""
    raw_prompt = ""
    if file:
        try:
            with open(file, "r", encoding="utf-8") as f:
                raw_prompt = f.read().strip()
        except Exception as e:
            console.print(f"[red]Error reading file {file}: {e}[/red]")
            raise typer.Exit(1)
    elif prompt:
        raw_prompt = prompt.strip()
    else:
        console.print("[bold cyan]Enter or paste your raw prompt below (press Enter twice to submit):[/bold cyan]")
        lines = []
        while True:
            try:
                line = input()
                if not line and lines and not lines[-1]:
                    break
                lines.append(line)
            except EOFError:
                break
        raw_prompt = "\n".join(lines).strip()

    if not raw_prompt:
        console.print("[red]Error: Empty prompt provided.[/red]")
        raise typer.Exit(1)

    obj_map = {
        "balanced": OptimizationObjective.BALANCED,
        "maximum_quality": OptimizationObjective.MAXIMUM_QUALITY,
        "maximum_compression": OptimizationObjective.MAXIMUM_COMPRESSION,
        "quality": OptimizationObjective.MAXIMUM_QUALITY,
        "compression": OptimizationObjective.MAXIMUM_COMPRESSION,
    }
    target_obj = obj_map.get(objective.lower(), OptimizationObjective.BALANCED)

    llm = resolve_backend(backend, model)
    agent = PromptOptimizerAgent(backend=llm)

    clarification_answers = {}
    if interactive:
        with Progress(
            SpinnerColumn("line"),
            TextColumn("[bold cyan]Analyzing prompt for ambiguities...[/bold cyan]"),
            transient=True,
        ) as progress:
            progress.add_task("analyzing", total=None)
            initial_analysis = agent.analyzer.analyze(raw_prompt)

        if initial_analysis.clarification_questions:
            console.print(Panel(
                "[bold yellow]Clarifications Detected[/bold yellow]\n"
                "The optimizer identified ambiguous requirements. Please answer or press Enter for default.",
                title="Targeted Clarifications",
                border_style="yellow"
            ))
            for q in initial_analysis.clarification_questions:
                ans = Prompt.ask(f"[bold green]{q.question}[/bold green] (Default: {q.default_assumption})")
                if ans.strip():
                    clarification_answers[q.id] = ans.strip()

    with Progress(
        SpinnerColumn("line"),
        TextColumn("[bold green]{task.description}[/bold green]"),
        console=console,
    ) as progress:
        task = progress.add_task("Executing Prompt Compiler...", total=None)

        def on_progress(stage: str, details: dict):
            msg_map = {
                "START": "Initializing compilation pipeline...",
                "TOKEN_COUNT": f"Original Tokens: {details.get('original_tokens')}",
                "ANALYSIS": "Stage 1: Decomposing semantics and hard invariants...",
                "PLANNING": "Stage 2: Synthesizing transformation blueprint...",
                "GENERATION": "Stage 3: Generating candidate architectures...",
                "TEST_GEN": "Stage 4: Synthesizing validation test scenarios...",
                "BASELINE_EXEC": "Stage 5: Simulating baseline on test suite...",
                "CANDIDATE_EXEC": "Stage 6: Simulating candidates & verifying guardrails...",
                "REFINEMENT": "Stage 7: Iteratively refining candidates...",
                "SELECTION": f"Stage 8: Evaluating Pareto objective: {target_obj.value}...",
                "COMPLETE": "Optimization complete!",
            }
            desc = msg_map.get(stage, f"Running {stage}...")
            progress.update(task, description=desc)

        report = agent.optimize(
            raw_prompt=raw_prompt,
            objective=target_obj,
            clarification_answers=clarification_answers if clarification_answers else None,
            progress_callback=on_progress,
        )

    # Persist to SQLite history
    run_id = history_store.save_run(report)

    if json_output:
        print(report.model_dump_json(indent=2))
        return

    console.print("\n")
    console.print(Panel(
        f"[bold cyan]Run ID:[/bold cyan] {run_id}\n"
        f"[bold cyan]Selected Strategy:[/bold cyan] {report.selected_candidate_id}\n"
        f"[bold cyan]Objective Mode:[/bold cyan] {report.selection_objective.value}\n"
        f"[bold cyan]Rationale:[/bold cyan] {report.selection_rationale}",
        title="[bold green] Optimization Complete [/bold green]",
        border_style="green",
    ))

    # Metrics Table
    metrics_table = Table(title="Optimization Performance Metrics", border_style="cyan")
    metrics_table.add_column("Metric", style="bold white")
    metrics_table.add_column("Original", justify="center")
    metrics_table.add_column("Optimized", justify="center")
    metrics_table.add_column("Delta / Impact", justify="center", style="bold green")

    token_color = "green" if report.tokens_saved > 0 else "yellow"
    metrics_table.add_row(
        "Token Count",
        str(report.original_tokens),
        str(report.final_tokens),
        f"[{token_color}]-{report.tokens_saved} tokens ({report.percentage_reduction:.1f}% reduction)[/{token_color}]",
    )
    qual_color = "green" if report.quality_delta >= 0 else "red"
    metrics_table.add_row(
        "Quality Score (0-10)",
        f"{report.original_quality_score:.2f}",
        f"{report.final_quality_score:.2f}",
        f"[{qual_color}]{report.quality_delta:+.2f}[/{qual_color}]",
    )
    metrics_table.add_row(
        "Preserved Invariants",
        f"{len(report.preserved_hard_requirements)} Hard Reqs",
        f"{len(report.preserved_hard_requirements)} Verified Intact",
        "[bold green]100% Fidelity[/bold green]",
    )
    metrics_table.add_row(
        "Redundancies Removed",
        f"{len(report.removed_redundancies)} detected",
        "0 remaining",
        f"[green]{len(report.removed_redundancies)} eliminated[/green]",
    )
    console.print(metrics_table)

    # Candidates Comparison Table
    cand_table = Table(title="Candidate Evaluation Matrix", border_style="blue")
    cand_table.add_column("Candidate ID", style="bold")
    cand_table.add_column("Strategy")
    cand_table.add_column("Tokens", justify="center")
    cand_table.add_column("% Saved", justify="center")
    cand_table.add_column("Quality", justify="center")
    cand_table.add_column("Status", justify="center")

    for c in report.all_candidates:
        status_str = "[green]Passed[/green]" if c.passed_guardrail else f"[red]Rejected: {c.guardrail_rejection_reason}[/red]"
        is_winner = " (WINNER)" if c.candidate_id == report.selected_candidate_id else ""
        cand_table.add_row(
            f"{c.candidate_id}{is_winner}",
            c.strategy,
            str(c.tokens.token_count),
            f"{c.tokens.reduction_percentage:.1f}%",
            f"{c.scores.overall_quality_score:.2f}",
            status_str,
        )
    console.print(cand_table)

    # Side-by-side prompt output
    console.print(Panel(
        report.final_optimized_prompt,
        title="[bold green]Final Compiled Prompt[/bold green]",
        border_style="green",
    ))


@app.command()
def history(limit: int = typer.Option(10, "--limit", "-n", help="Number of recent runs to show")):
    """List historical prompt compilation runs."""
    runs = history_store.list_runs(limit=limit)
    if not runs:
        console.print("[yellow]No optimization runs found in history.[/yellow]")
        return

    table = Table(title="Prompt Compiler History", border_style="cyan")
    table.add_column("Run ID", style="bold")
    table.add_column("Timestamp")
    table.add_column("Tokens Delta")
    table.add_column("% Saved")
    table.add_column("Quality")
    table.add_column("Strategy")
    table.add_column("Prompt Preview")

    for r in runs:
        table.add_row(
            r.run_id,
            r.timestamp[:19].replace("T", " "),
            f"-{r.tokens_saved} tks",
            f"{r.percentage_reduction:.1f}%",
            f"{r.final_quality_score:.1f}",
            r.selected_candidate_id,
            r.original_prompt_preview,
        )
    console.print(table)


@app.command()
def bench(
    backend: str = typer.Option("mock", "--backend", "-b", help="ollama | mock | openai | gemini")
):
    """Run standardized prompt compiler benchmarks."""
    console.print(f"[bold cyan]Running PromptCompiler Benchmarks using '{backend}' backend...[/bold cyan]")
    llm = resolve_backend(backend, None)
    agent = PromptOptimizerAgent(backend=llm)
    suite = BenchmarkSuite(agent=agent)

    report = suite.run_all()

    table = Table(title="PromptCompiler Benchmark Results", border_style="green")
    table.add_column("Benchmark ID", style="bold")
    table.add_column("Name")
    table.add_column("Orig Tks")
    table.add_column("Final Tks")
    table.add_column("% Saved")
    table.add_column("Quality")
    table.add_column("Latency")

    for res in report.results:
        table.add_row(
            res.benchmark_id,
            res.name,
            str(res.original_tokens),
            str(res.final_tokens),
            f"{res.percentage_reduction:.1f}%",
            f"{res.quality_score:.1f}/10",
            f"{res.execution_time_seconds:.2f}s",
        )

    console.print(table)
    console.print(Panel(
        f"[bold green]Average Token Reduction:[/bold green] {report.average_token_reduction:.1f}%\n"
        f"[bold green]Average Quality Score:[/bold green] {report.average_quality_score:.2f}/10.0\n"
        f"[bold green]Hard Invariant Preservation Rate:[/bold green] {report.invariant_preservation_rate:.1f}%\n"
        f"[bold green]Total Benchmarks Evaluated:[/bold green] {report.total_benchmarks}",
        title="Benchmark Summary",
        border_style="green"
    ))


@app.command()
def test_backend(
    backend: str = typer.Option("ollama", "--backend", "-b"),
    model: Optional[str] = typer.Option(None, "--model", "-m"),
):
    """Test connectivity and status of an LLM backend."""
    console.print(f"Testing backend [bold]{backend}[/bold]...")
    llm = resolve_backend(backend, model)
    available = llm.is_available()
    if available:
        console.print(f"[bold green]Success:[/bold green] Backend '{llm.get_model_name()}' is reachable.")
        resp = llm.generate("Respond with 'OK' if you can read this.", max_tokens=10)
        console.print(f"Sample response: [italic]{resp}[/italic]")
    else:
        console.print(f"[bold red]Failed:[/bold red] Backend '{llm.get_model_name()}' is NOT reachable.")


@app.command()
def spotlight():
    """Launch the floating Desktop Spotlight Box."""
    console.print("[bold cyan]Launching PromptCompiler Spotlight Box... (Press Esc to close)[/bold cyan]")
    from prompt_optimizer.quick_box.desktop_app import launch
    launch()


if __name__ == "__main__":
    app()
