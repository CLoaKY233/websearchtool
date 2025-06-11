from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SearchResultType(Enum):
    """Types of search results"""

    WEB = "web"
    IMAGE = "image"
    NEWS = "news"
    VIDEO = "video"


class SearchStatus(Enum):
    """Search operation status"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"


@dataclass
class SearchResult:
    """Individual search result from any search provider"""

    title: str
    url: str
    snippet: str
    result_type: SearchResultType = SearchResultType.WEB
    metadata: Dict[str, Any] = Field(default_factory=dict)
    rank: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.now)


@dataclass
class SearchResponse:
    """Complete search response with metadata"""

    query: str
    results: List[SearchResult]
    total_results: Optional[int] = None
    search_time: float = 0.0
    status: SearchStatus = SearchStatus.COMPLETED
    provider: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None


class SearchRequest(BaseModel):
    """Pydantic model for search requests"""

    query: str = Field(
        ..., min_length=1, max_length=500, description="Search query"
    )
    max_results: int = Field(
        default=10, ge=1, le=100, description="Maximum number of results"
    )
    result_type: SearchResultType = Field(
        default=SearchResultType.WEB, description="Type of search results"
    )
    safe_search: bool = Field(default=True, description="Enable safe search")
    language: Optional[str] = Field(default="en", description="Search language")
    region: Optional[str] = Field(default=None, description="Search region")
    date_restrict: Optional[str] = Field(
        default=None,
        description="Date restriction (e.g., 'd1', 'w1', 'm1', 'y1')",
    )


class SearchProviderInterface(ABC):
    """Abstract interface for search providers"""

    @abstractmethod
    async def search(self, request: SearchRequest) -> SearchResponse:
        """Perform search and return results"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the search provider is available"""
        pass

    @abstractmethod
    def get_rate_limit_info(self) -> Dict[str, Any]:
        """Get current rate limit information"""
        pass


class CacheInterface(ABC):
    """Abstract interface for caching search results"""

    @abstractmethod
    async def get(self, key: str) -> Optional[SearchResponse]:
        """Get cached search response"""
        pass

    @abstractmethod
    async def set(
        self, key: str, value: SearchResponse, ttl: int = 3600
    ) -> bool:
        """Cache search response with TTL in seconds"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete cached entry"""
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cached entries"""
        pass


class RateLimiterInterface(ABC):
    """Abstract interface for rate limiting"""

    @abstractmethod
    async def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed under rate limits"""
        pass

    @abstractmethod
    async def record_request(self, identifier: str) -> None:
        """Record a request for rate limiting"""
        pass

    @abstractmethod
    async def get_remaining_requests(self, identifier: str) -> int:
        """Get remaining requests for identifier"""
        pass


class SearchServiceInterface(ABC):
    """Main search service interface"""

    @abstractmethod
    async def search(self, request: SearchRequest) -> SearchResponse:
        """Perform search with caching and rate limiting"""
        pass

    @abstractmethod
    async def bulk_search(
        self, requests: List[SearchRequest]
    ) -> List[SearchResponse]:
        """Perform multiple searches efficiently"""
        pass

    @abstractmethod
    async def get_search_suggestions(self, partial_query: str) -> List[str]:
        """Get search suggestions for partial query"""
        pass
