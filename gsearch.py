#!/usr/bin/env python3
"""
Enhanced CLI with integrated async web crawler.
Run:      python gsearch.py "openai function calling"
Interactive: python gsearch.py
"""

import asyncio
import time
from collections import defaultdict, deque
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse, urlunparse

import aiohttp
import typer
from bs4 import BeautifulSoup
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from typing_extensions import Annotated

from src.config.settings import settings
from src.search import GoogleSearchService

app = typer.Typer(help="Google Search + Web Crawler CLI")
console = Console()

service = GoogleSearchService()


class AsyncWebCrawler:
    """
    High-performance async web crawler for discovering subsites.
    Uses semaphore-based concurrency control and rate limiting[33][36].
    """

    def __init__(
        self,
        max_concurrent: int = 8,
        max_depth: int = 2,
        max_pages_per_domain: int = 8,
        delay: float = 1.0,
    ):
        self.max_concurrent = max_concurrent
        self.max_depth = max_depth
        self.max_pages_per_domain = max_pages_per_domain
        self.delay = delay
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.session: Optional[aiohttp.ClientSession] = None

        # Tracking structures
        self.visited_urls: Set[str] = set()
        self.domain_page_count: Dict[str, int] = defaultdict(int)
        self.crawl_queue: Dict[str, deque] = defaultdict(deque)
        self.discovered_links: Dict[str, Set[str]] = defaultdict(set)

        # Headers for polite crawling[33]
        self.headers = {
            "User-Agent": "AsyncWebCrawler/1.0 (+http://example.com/bot)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def __aenter__(self):
        """Async context manager entry[29]"""
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers=self.headers,
            connector=aiohttp.TCPConnector(limit=100, limit_per_host=10),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit[29]"""
        if self.session:
            await self.session.close()

    def normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments and query params for deduplication[15]"""
        parsed = urlparse(url)
        return urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                "",
                "",
                "",  # Remove params, query, fragment
            )
        )

    def get_domain(self, url: str) -> str:
        """Extract domain from URL[34]"""
        return urlparse(url).netloc.lower()

    def is_valid_url(self, url: str, base_domain: str) -> bool:
        """Check if URL is valid for crawling[34]"""
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False

            # Only crawl same domain
            current_domain = parsed.netloc.lower()
            if current_domain != base_domain:
                return False

            # Skip certain file types
            path = parsed.path.lower()
            skip_extensions = (
                ".pdf",
                ".doc",
                ".docx",
                ".xls",
                ".xlsx",
                ".ppt",
                ".pptx",
                ".zip",
                ".rar",
                ".tar",
                ".gz",
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".svg",
                ".mp4",
                ".avi",
                ".mp3",
                ".wav",
                ".css",
                ".js",
            )

            return not path.endswith(skip_extensions)
        except:
            return False

    async def fetch_page(self, url: str) -> Tuple[str, str, int]:
        """
        Fetch a single page with error handling and rate limiting[32][35].
        Returns (url, content, status_code)
        """
        async with self.semaphore:  # Limit concurrent requests[36]
            try:
                # Rate limiting delay[33]
                await asyncio.sleep(self.delay)

                async with self.session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        return url, content, response.status
                    else:
                        return url, "", response.status

            except asyncio.TimeoutError:
                console.print(f"[yellow]Timeout: {url}[/yellow]")
                return url, "", 408
            except Exception as e:
                console.print(f"[red]Error fetching {url}: {str(e)}[/red]")
                return url, "", 500

    def extract_links(self, html_content: str, base_url: str) -> Set[str]:
        """Extract and normalize links from HTML content[18][20]"""
        links = set()
        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Find all anchor tags with href attributes[18]
            for link in soup.find_all("a", href=True):
                href = link.get("href")
                if href:
                    # Convert relative URLs to absolute[15]
                    absolute_url = urljoin(base_url, href)
                    normalized_url = self.normalize_url(absolute_url)
                    links.add(normalized_url)

        except Exception as e:
            console.print(f"[red]Error parsing HTML: {str(e)}[/red]")

        return links

    async def crawl_domain(self, start_url: str) -> Dict[str, Set[str]]:
        """
        Crawl a single domain to discover subsites[16][17].
        Returns mapping of depth -> discovered URLs
        """
        domain = self.get_domain(start_url)

        # Initialize crawling for this domain
        self.crawl_queue[domain].append((start_url, 0))  # (url, depth)
        discovered_by_depth = defaultdict(set)

        console.print(f"[blue]🕷️  Crawling domain: {domain}[/blue]")

        # Create tasks for concurrent crawling[32]
        tasks = []

        while (
            self.crawl_queue[domain]
            and self.domain_page_count[domain] < self.max_pages_per_domain
        ):
            current_batch = []

            # Process batch of URLs
            for _ in range(
                min(self.max_concurrent, len(self.crawl_queue[domain]))
            ):
                if not self.crawl_queue[domain]:
                    break

                url, depth = self.crawl_queue[domain].popleft()

                if (
                    url in self.visited_urls
                    or depth > self.max_depth
                    or self.domain_page_count[domain]
                    >= self.max_pages_per_domain
                ):
                    continue

                current_batch.append((url, depth))
                self.visited_urls.add(url)
                self.domain_page_count[domain] += 1

            if not current_batch:
                break

            # Fetch batch concurrently[30][32]
            tasks = [self.fetch_page(url) for url, depth in current_batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results and extract new links
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    continue

                url, content, status_code = result
                original_depth = current_batch[i][1]

                if status_code == 200 and content:
                    discovered_by_depth[original_depth].add(url)

                    # Extract links for next depth level
                    if original_depth < self.max_depth:
                        new_links = self.extract_links(content, url)

                        for link in new_links:
                            if (
                                self.is_valid_url(link, domain)
                                and link not in self.visited_urls
                                and self.domain_page_count[domain]
                                < self.max_pages_per_domain
                            ):
                                self.crawl_queue[domain].append(
                                    (link, original_depth + 1)
                                )

        return dict(discovered_by_depth)

    async def crawl_multiple_domains(
        self, urls: List[str]
    ) -> Dict[str, Dict[str, Set[str]]]:
        """
        Crawl multiple domains concurrently[31].
        Returns mapping of domain -> depth -> URLs
        """
        console.print(
            f"[green]🚀 Starting concurrent crawl of {len(urls)} domains[/green]"
        )

        # Group URLs by domain to avoid duplicate work
        domains_to_crawl = {}
        for url in urls:
            domain = self.get_domain(url)
            if domain not in domains_to_crawl:
                domains_to_crawl[domain] = url

        # Create tasks for each domain[30]
        crawl_tasks = [
            self.crawl_domain(start_url)
            for start_url in domains_to_crawl.values()
        ]

        # Execute all crawl tasks concurrently[31]
        results = await asyncio.gather(*crawl_tasks, return_exceptions=True)

        # Organize results by domain
        domain_results = {}
        for i, result in enumerate(results):
            if not isinstance(result, Exception):
                domain = list(domains_to_crawl.keys())[i]
                domain_results[domain] = result

        return domain_results


def display_crawl_results(crawl_results: Dict[str, Dict[str, Set[str]]]):
    """Display crawling results in a formatted table"""
    if not crawl_results:
        console.print("[yellow]No crawling results to display[/yellow]")
        return

    console.print("\n" + "=" * 80)
    console.print("[bold blue]🗺️  DISCOVERED SITE STRUCTURE[/bold blue]")
    console.print("=" * 80)

    for domain, depth_results in crawl_results.items():
        console.print(f"\n[bold green]📍 Domain: {domain}[/bold green]")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Depth", style="cyan", width=10)
        table.add_column("URLs Found", style="white", width=70)

        total_urls = 0
        for depth in sorted(depth_results.keys()):
            urls = depth_results[depth]
            total_urls += len(urls)

            # Limit display to first 3 URLs per depth
            url_list = list(urls)[:3]
            url_display = "\n".join(url_list)
            if len(urls) > 3:
                url_display += f"\n... and {len(urls) - 3} more"

            table.add_row(str(depth), url_display)

        table.add_row("", "")
        table.add_row("[bold]Total", f"[bold]{total_urls} URLs discovered")
        console.print(table)


async def search_and_crawl(
    query: str, num_results: int = 5, crawl_enabled: bool = True
):
    """
    Perform Google search and optionally crawl discovered websites[4].
    """
    console.print(f"[blue]🔍 Searching Google for: '{query}'[/blue]")

    # Get Google search results
    search_data = await service.search(query, num_results)
    if not search_data:
        console.print("[red]No search results found[/red]")
        return

    # Display search results
    console.print(service.format_results(search_data))

    if not crawl_enabled:
        return

    # Extract URLs from search results for crawling
    urls_to_crawl = []
    if "items" in search_data:
        for item in search_data["items"]:
            if "link" in item:
                urls_to_crawl.append(item["link"])

    if not urls_to_crawl:
        console.print("[yellow]No URLs found to crawl[/yellow]")
        return

    console.print(
        f"\n[blue]🕷️  Initiating async crawl of {len(urls_to_crawl)} websites...[/blue]"
    )

    # Perform async crawling[10]
    start_time = time.time()

    async with AsyncWebCrawler(
        max_concurrent=8, max_depth=2, max_pages_per_domain=8, delay=1.0
    ) as crawler:
        crawl_results = await crawler.crawl_multiple_domains(urls_to_crawl)

    crawl_time = time.time() - start_time
    console.print(
        f"[green]✅ Crawling completed in {crawl_time:.2f} seconds[/green]"
    )

    # Display results
    display_crawl_results(crawl_results)


@app.command()
def search(
    query: Annotated[Optional[str], typer.Argument()] = None,
    crawl: Annotated[bool, typer.Option("--crawl/--no-crawl")] = True,
    results: Annotated[int, typer.Option("--results", "-n")] = 5,
):
    """
    Perform Google search with optional website crawling.
    """

    async def _run(q: str):
        await search_and_crawl(q, results, crawl)

    if query:
        asyncio.run(_run(query))
    else:
        asyncio.run(interactive())


async def interactive():
    """
    Enhanced interactive mode with crawling options[32].
    """
    console.print(
        "[bold blue]🔍 Google Search + Web Crawler Interactive Mode[/bold blue]"
    )
    console.print(
        "[dim]Commands: 'search <query>', 'crawl on/off', 'exit'[/dim]"
    )

    crawl_enabled = True

    while True:
        user_input = Prompt.ask("\n[bold green]Search[/bold green]").strip()

        if user_input.lower() in {"exit", "quit", "q"}:
            console.print("👋 Goodbye!")
            break

        if user_input.lower().startswith("crawl "):
            setting = user_input.split(" ", 1)[1].lower()
            if setting in ["on", "true", "yes"]:
                crawl_enabled = True
                console.print("[green]✅ Crawling enabled[/green]")
            elif setting in ["off", "false", "no"]:
                crawl_enabled = False
                console.print("[yellow]❌ Crawling disabled[/yellow]")
            continue

        if not user_input:
            continue

        # Extract query (remove 'search' prefix if present)
        query = user_input
        if query.lower().startswith("search "):
            query = query[7:]

        await search_and_crawl(
            query, settings.default_num_results, crawl_enabled
        )


if __name__ == "__main__":
    app()
