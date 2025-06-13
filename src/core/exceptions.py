class SearchException(Exception):
    """Base exception for google search service"""

    pass


class APIRequestException(SearchException):
    """Raised on HTTP / API errors"""

    pass


class CacheMissException(SearchException):
    """Raise when expected cache entry is missing"""

    pass


class LLMException(SearchException):
    """Errors raised by any LLM implementation"""

    ...
