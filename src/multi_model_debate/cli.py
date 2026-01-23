"""CLI interface for adversarial critique."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from multi_model_debate import __version__
from multi_model_debate.config import load_config
from multi_model_debate.exceptions import AdversarialReviewError
from multi_model_debate.orchestrator import Orchestrator

app = typer.Typer(
    name="multi-model-debate",
    help="Multi-model debate engine for stress-testing proposals before implementation.",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"multi-model-debate {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-V",
            help="Show version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """Multi-Model Debate - Multi-model debate for stress-testing proposals."""
    pass


@app.command()
def start(
    game_plan: Annotated[
        Path | None,
        typer.Argument(
            help="Path to game plan file, or '-' for stdin.",
        ),
    ] = None,
    stdin: Annotated[
        bool,
        typer.Option(
            "--stdin",
            help="Read game plan from stdin.",
        ),
    ] = False,
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            help="Path to config file (default: auto-detect).",
        ),
    ] = None,
    runs_dir: Annotated[
        Path | None,
        typer.Option(
            "--runs-dir",
            "-r",
            help="Directory for run outputs (default: ./runs).",
        ),
    ] = None,
    skip_protocol: Annotated[
        bool,
        typer.Option(
            "--skip-protocol",
            help="Skip the pre-debate protocol entirely.",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Enable verbose logging.",
        ),
    ] = False,
) -> None:
    """Start a new adversarial review.

    The game plan should be a markdown document describing the proposal
    to be stress-tested. Provide via file path or stdin:

      multi-model-debate start proposal.md
      multi-model-debate start --stdin < proposal.md
      multi-model-debate start -              # alias for --stdin
    """
    # Handle '-' as alias for --stdin
    use_stdin = stdin or (game_plan is not None and str(game_plan) == "-")

    # Validate mutual exclusion
    if use_stdin and game_plan is not None and str(game_plan) != "-":
        console.print("[red]Error:[/red] Cannot use --stdin with a file path")
        raise typer.Exit(1)

    if not use_stdin and game_plan is None:
        console.print("[red]Error:[/red] Provide a game plan file or use --stdin")
        raise typer.Exit(1)

    try:
        cfg = load_config(config)
        runs = runs_dir or Path.cwd() / "runs"

        orchestrator = Orchestrator(config=cfg, runs_dir=runs)

        # Create run directory FIRST so progress is tracked and resumable
        if use_stdin:
            content = sys.stdin.read()
            if not content.strip():
                console.print("[red]Error:[/red] stdin is empty")
                raise typer.Exit(1)
            context = orchestrator.start_from_content(content)
        else:
            # Type narrowing: game_plan is not None here (checked at line 114-116)
            assert game_plan is not None
            # Validate file exists (since we removed exists=True from Argument)
            if not game_plan.exists():
                console.print(f"[red]Error:[/red] File not found: {game_plan}")
                raise typer.Exit(1)
            if not game_plan.is_file():
                console.print(f"[red]Error:[/red] Not a file: {game_plan}")
                raise typer.Exit(1)
            context = orchestrator.start(game_plan)

        # Run pre-debate protocol (saved to run directory for resume)
        orchestrator.run_pre_debate_protocol(
            context=context,
            skip_protocol=skip_protocol,
        )

        orchestrator.execute(context)

    except AdversarialReviewError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise typer.Exit(130) from None


@app.command()
def resume(
    run_dir: Annotated[
        Path | None,
        typer.Option(
            "--run",
            "-r",
            help="Specific run directory to resume (default: latest incomplete).",
        ),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            help="Path to config file (default: auto-detect).",
        ),
    ] = None,
    runs_dir: Annotated[
        Path | None,
        typer.Option(
            "--runs-dir",
            help="Directory containing runs (default: ./runs).",
        ),
    ] = None,
) -> None:
    """Resume an incomplete adversarial review.

    Continues from the last checkpoint, skipping already-completed phases.
    Useful after interruptions or failures.
    """
    try:
        cfg = load_config(config)
        runs = runs_dir or Path.cwd() / "runs"

        orchestrator = Orchestrator(config=cfg, runs_dir=runs)
        context = orchestrator.resume(run_dir)

        # Run pre-debate protocol if not already complete
        # This handles runs that were interrupted during pre-debate
        orchestrator.run_pre_debate_protocol(context=context)

        orchestrator.execute(context)

    except AdversarialReviewError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise typer.Exit(130) from None


@app.command()
def status(
    runs_dir: Annotated[
        Path | None,
        typer.Option(
            "--runs-dir",
            "-r",
            help="Directory containing runs (default: ./runs).",
        ),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            help="Path to config file (default: auto-detect).",
        ),
    ] = None,
) -> None:
    """Show status of the most recent run.

    Displays the current state, completed phases, and game plan
    for the latest review run.
    """
    try:
        cfg = load_config(config)
        runs = runs_dir or Path.cwd() / "runs"

        orchestrator = Orchestrator(config=cfg, runs_dir=runs)
        run_status = orchestrator.status()

        if run_status is None:
            console.print("[yellow]No runs found[/yellow]")
            raise typer.Exit(0)

        # Display status
        console.print()
        console.print("[bold]Latest Run Status[/bold]")
        console.print()

        table = Table(show_header=False, box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value")

        table.add_row("Run", run_status["run_dir"])
        table.add_row("Status", _format_status(run_status["status"]))
        table.add_row("Game Plan", run_status.get("game_plan") or "N/A")

        console.print(table)
        console.print()

        # Completed phases
        phases = run_status.get("completed_phases", [])
        if phases:
            console.print("[bold]Completed Phases:[/bold]")
            for phase in phases:
                console.print(f"  [green]\u2713[/green] {phase}")
        else:
            console.print("[dim]No phases completed yet[/dim]")

        console.print()

    except AdversarialReviewError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None


def _format_status(status: str) -> str:
    """Format status with color."""
    colors = {
        "completed": "[green]completed[/green]",
        "in_progress": "[yellow]in progress[/yellow]",
        "failed": "[red]failed[/red]",
        "unknown": "[dim]unknown[/dim]",
    }
    return colors.get(status, status)


if __name__ == "__main__":
    app()
