from typing import Any, Dict, Optional

from ..config.settings import settings
from ..core.exceptions import CacheMissException
from ..core.interfaces import SearchInterface
from .cache import LRUCache
from .client import GoogleCSEClient
from .formatter import pretty_print


class GoogleSearchService(SearchInterface):
    """
    Facade that orchestrates HTTP client, cache and formatter.
    This is analogous to RAGEngine acting as a façade over ReflexionRAGEngine[1].
    """

    def __init__(self):
        super().__init__()
        self._client = GoogleCSEClient()
        self._cache = (
            LRUCache(settings.max_cache_size) if settings.enable_cache else None
        )

    async def search(
        self, query: str, num_results: int
    ) -> Optional[Dict[Any, Any]]:
        # Check cache first
        if self._cache:
            try:
                return self._cache.get(query)
            except CacheMissException:
                pass

        data = await self._client.fetch(query, num_results)

        if self._cache and data:
            self._cache.put(query, data)
        return data

    def format_results(self, search_data: Dict[Any, Any]) -> str:
        return pretty_print(search_data)
