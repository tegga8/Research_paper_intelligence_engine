"""Rich-powered terminal rendering with plain-text fallbacks."""

from __future__ import annotations

from contextlib import contextmanager
import importlib.util
from typing import Iterable, Sequence

from database import Paper

RICH_AVAILABLE = importlib.util.find_spec("rich") is not None
if RICH_AVAILABLE:
    from rich import box
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table

    console = Console()
else:
    box = None
    Markdown = None
    Panel = None
    Progress = None
    SpinnerColumn = None
    TextColumn = None
    Table = None
    console = None


def header(current_topic: str | None, total_papers: int = 0, clusters: int = 0) -> None:
    title = "Research Paper Intelligence Engine"
    if RICH_AVAILABLE:
        console.print(
            Panel.fit(
                f"[bold cyan]{title}[/bold cyan]\n\n"
                f"[bold]Current Topic:[/bold] {current_topic or 'None'}\n"
                f"[bold]Total Papers:[/bold] {total_papers}\n"
                f"[bold]Clusters:[/bold] {clusters}",
                border_style="cyan",
                box=box.DOUBLE,
            )
        )
    else:
        print("\n" + "=" * 88)
        print(title)
        print(f"Current Topic: {current_topic or 'None'} | Total Papers: {total_papers} | Clusters: {clusters}")
        print("=" * 88)


def menu() -> None:
    options = [
        ("1", "Download papers from ArXiv"),
        ("2", "Dashboard"),
        ("3", "Semantic vector search"),
        ("4", "Cluster papers"),
        ("5", "Recommend Similar Papers"),
        ("6", "Research Gap Discovery"),
        ("7", "Research Trend Dashboard"),
        ("8", "Generate literature review"),
        ("9", "Export reports"),
        ("10", "Switch saved topic"),
        ("0", "Exit"),
    ]
    if RICH_AVAILABLE:
        table = Table(show_header=False, box=box.SIMPLE, border_style="blue")
        table.add_column("Option", style="bold cyan", width=6)
        table.add_column("Action")
        for key, label in options:
            table.add_row(key, label)
        console.print(table)
    else:
        for key, label in options:
            print(f"{key}. {label}")


def table(title: str, columns: Sequence[str], rows: Iterable[Sequence[object]]) -> None:
    if RICH_AVAILABLE:
        rich_table = Table(title=title, box=box.ROUNDED, show_lines=False)
        for column in columns:
            rich_table.add_column(column, overflow="fold")
        for row in rows:
            rich_table.add_row(*[str(value) for value in row])
        console.print(rich_table)
    else:
        print(f"\n{title}")
        print(" | ".join(columns))
        print("-" * 88)
        for row in rows:
            print(" | ".join(str(value) for value in row))


def paper_panel(paper: Paper, score: float | None = None) -> None:
    title = f"{paper.title}"
    if score is not None:
        title = f"Score {score:.3f} | {title}"
    body = (
        f"Authors: {paper.authors[:140]}\n"
        f"Published: {paper.published_at} | Categories: {paper.categories} | Cluster: {paper.cluster}\n\n"
        f"{paper.abstract}\n\nPDF: {paper.pdf_url}"
    )
    if RICH_AVAILABLE:
        console.print(Panel(body, title=title, border_style="green"))
    else:
        print(f"\n{title}\n{body}")


def markdown(content: str) -> None:
    if RICH_AVAILABLE:
        console.print(Markdown(content))
    else:
        print(content)


def info(message: str) -> None:
    if RICH_AVAILABLE:
        console.print(f"[cyan]ℹ[/cyan] {message}")
    else:
        print(message)


def success(message: str) -> None:
    if RICH_AVAILABLE:
        console.print(f"[green]✓[/green] {message}")
    else:
        print(message)


def warning(message: str) -> None:
    if RICH_AVAILABLE:
        console.print(f"[yellow]⚠[/yellow] {message}")
    else:
        print(message)


@contextmanager
def spinner(message: str):
    if RICH_AVAILABLE:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
            progress.add_task(message, total=None)
            yield
    else:
        print(message)
        yield
