from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class SearchInterface(ABC):
    """Abstract interface for any search"""

    @abstractmethod
    async def search(
        self, query: str, num_results: int
    ) -> Optional[Dict[Any, Any]]:
        """Perform a search and return raw json (or None on failure)"""
        ...

    @abstractmethod
    def format_results(self, search_data: Dict[Any, Any]) -> str:
        """Return prettified string for terminal display"""
        ...
