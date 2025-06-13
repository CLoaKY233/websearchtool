# websearchtool/src/cli.py
"""
One-stop command-line interface for the Web Search → LLM ranking → optional
crawling pipeline.

Run with:
    python -m websearchtool.src.cli "your question" --results 10 --top-k 3 --crawl
"""

from __future__ import annotations

import argparse
import asyncio
import re
from typing import List, Set
from urllib.parse import urljoin, urlparse

import aiohttp
from rich.console import Console
from rich.table import Table

from src.config.settings import settings
from src.llm.github_llm import GitHubLLM
from src.search import GoogleSearchService  # search facade[1]
from src.services.serp_ranker import SERPRanker  # LLM ranker[1]
from src.utils.logging import logger  # shared logger[1]

console = Console()


# ---------------------------------------------------------------------------#
#                               HTML-crawler                                 #
# ---------------------------------------------------------------------------#
_HREF_RE = re.compile(r'href=["\'](?P<url>[^"\']+)["\']', re.I)


async def _fetch_html(session: aiohttp.ClientSession, url: str) -> str:
    """Download raw HTML (best-effort, short timeout)."""
    try:
        async with session.get(url, timeout=settings.http_timeout) as resp:
            resp.raise_for_status()
            return await resp.text()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Crawl failed", url=url, error=str(exc))
        return ""


def _extract_links(base_url: str, html: str, limit: int = 10) -> List[str]:
    """Return up-to *limit* absolute URLs found in the page."""
    links: List[str] = []
    for match in _HREF_RE.finditer(html):
        href: str = match.group("url")
        # ignore anchors / javascript / mailto
        if href.startswith(("javascript:", "mailto:", "#")):
            continue
        abs_url = urljoin(base_url, href)
        # keep same scheme (http/https) only
        if urlparse(abs_url).scheme in {"http", "https"}:
            links.append(abs_url)
        if len(links) >= limit:
            break
    return links


async def crawl_and_collect(urls: List[str], per_site: int = 10) -> List[str]:
    """Fetch each URL concurrently and aggregate unique outbound links."""
    collected: Set[str] = set()
    headers = {"User-Agent": "websearchtool/1.0 (+https://example.com)"}
    timeout = aiohttp.ClientTimeout(total=settings.http_timeout)

    async with aiohttp.ClientSession(
        headers=headers, timeout=timeout
    ) as session:
        tasks = [_fetch_html(session, url) for url in urls]
        for url, html in zip(
            urls, await asyncio.gather(*tasks, return_exceptions=True)
        ):
            if isinstance(html, str) and html:
                collected.update(_extract_links(url, html, per_site))
    return sorted(collected)


# ---------------------------------------------------------------------------#
#                                  CLI                                       #
# ---------------------------------------------------------------------------#
async def run(query: str, num_results: int, top_k: int, crawl: bool) -> None:
    search_service = GoogleSearchService()
    llm = GitHubLLM()
    ranker = SERPRanker(llm, top_k=top_k)

    # 1️⃣ Google Custom Search
    console.print(f"[bold blue]🔍 Searching:[/] {query}")
    search_data = await search_service.search(query, num_results)
    if not search_data or "items" not in search_data:
        console.print("[red]No search results found.[/red]")
        return

    # 2️⃣ LLM-based relevance ranking
    ranked = await ranker.rank(query, search_data)
    if not ranked:
        console.print("[red]Ranking failed, nothing to show.[/red]")
        return

    table = Table(title="Top-ranked SERPs", show_lines=True)
    table.add_column("#", style="bold cyan", width=3)
    table.add_column("Score", style="magenta", width=7, justify="right")
    table.add_column("Title", style="white")
    table.add_column("URL", style="green")

    for i, item in enumerate(ranked, 1):
        table.add_row(
            str(i),
            f"{item.get('serp_score', '?')}/10",
            item.get("title", "—"),
            item.get("link", "—"),
        )

    console.print(table)

    # 3️⃣ Optional crawling
    if crawl:
        urls_to_crawl: List[str] = [it["link"] for it in ranked if "link" in it]
        console.print(
            f"\n[bold blue]🕸️ Crawling top {len(urls_to_crawl)} pages …[/bold blue]"
        )
        discovered: List[str] = await crawl_and_collect(urls_to_crawl)

        if discovered:
            console.print(
                f"\n[bold green]Discovered {len(discovered)} links:[/bold green]"
            )
            for link in discovered:
                console.print(f" • {link}")
        else:
            console.print("[yellow]No outbound links found.[/yellow]")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="websearchtool",
        description="Google-search + GitHub-LLM ranking CLI",
    )
    parser.add_argument("query", help="search phrase")
    parser.add_argument(
        "--results",
        type=int,
        default=settings.default_num_results,
        help=f"How many Google results to fetch (1-10, default {settings.default_num_results})",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Keep the K highest-scored SERPs (default 3)",
    )
    parser.add_argument(
        "--crawl",
        action="store_true",
        help="Fetch each top-ranked page and list outbound links",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    try:
        asyncio.run(
            run(
                query=args.query,
                num_results=args.results,
                top_k=args.top_k,
                crawl=args.crawl,
            )
        )
    except KeyboardInterrupt:
        console.print("\n[red]Interrupted by user.[/red]")


if __name__ == "__main__":  # pragma: no cover
    main()
