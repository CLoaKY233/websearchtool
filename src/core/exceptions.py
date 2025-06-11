from typing import Any, Dict, Optional


class WebSearchException(Exception):
    """Base exception for web search tool"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class SearchProviderException(WebSearchException):
    """Search provider-related exceptions"""

    pass


class GoogleSearchException(SearchProviderException):
    """Google Custom Search API specific exceptions"""

    pass


class RateLimitException(WebSearchException):
    """Rate limiting exceptions"""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs: Any,
    ):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class CacheException(WebSearchException):
    """Cache-related exceptions"""

    pass


class ValidationException(WebSearchException):
    """Request validation exceptions"""

    pass


class TimeoutException(WebSearchException):
    """Timeout-related exceptions"""

    pass


class AuthenticationException(WebSearchException):
    """Authentication-related exceptions"""

    pass


class QuotaExceededException(WebSearchException):
    """API quota exceeded exceptions"""

    def __init__(
        self,
        message: str = "API quota exceeded",
        quota_type: Optional[str] = None,
        reset_time: Optional[int] = None,
        **kwargs: Any,
    ):
        super().__init__(message, **kwargs)
        self.quota_type = quota_type
        self.reset_time = reset_time


class ConfigurationException(WebSearchException):
    """Configuration-related exceptions"""

    pass


class NetworkException(WebSearchException):
    """Network-related exceptions"""

    pass


class ParseException(WebSearchException):
    """Response parsing exceptions"""

    pass
