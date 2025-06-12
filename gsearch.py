#!/usr/bin/env python3
"""
CLI entry-point mirroring rag/rag.py[1].
Run:      python gsearch.py "openai function calling"
Interactive: python gsearch.py
"""

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Prompt
from typing_extensions import Annotated

from src.config.settings import settings
from src.search import GoogleSearchService

app = typer.Typer(help="Google Custom Search CLI")
console = Console()

service = GoogleSearchService()


@app.command()
def search(query: Annotated[Optional[str], typer.Argument()] = None):
    """
    One-shot search.
    """

    async def _run(q: str):
        data = await service.search(q, settings.default_num_results)
        console.print(service.format_results(data or {}))

    if query:
        asyncio.run(_run(query))
    else:
        asyncio.run(interactive())


async def interactive():
    """
    Rich interactive mode.
    """
    console.print("[bold blue]🔍 Google Search Interactive Mode[/bold blue]")
    console.print("[dim]Type 'exit' to quit.[/dim]")

    while True:
        q = Prompt.ask("\n[bold green]Query[/bold green]").strip()
        if q.lower() in {"exit", "quit", "q"}:
            console.print("👋 Bye!")
            break
        if not q:
            continue
        data = await service.search(q, settings.default_num_results)
        console.print(service.format_results(data or {}))


if __name__ == "__main__":
    app()
