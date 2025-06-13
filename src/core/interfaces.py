from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, Optional


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


@dataclass
class StreamingChunk:
    content: str
    is_complete: bool = False
    usage_info: Optional[Dict[str, Any]] = None


class LLMInterface(ABC):
    """Contract for any Large-Language-Model implementation"""

    @abstractmethod
    async def complete(
        self, prompt: str, **kwargs: Any
    ) -> str:  # full text completion
        ...

    @abstractmethod
    def stream(
        self, prompt: str, **kwargs: Any
    ) -> AsyncIterator[StreamingChunk]: ...
