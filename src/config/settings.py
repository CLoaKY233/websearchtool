# websearchtool/src/config/settings.py
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Web Search Tool settings with environment variable support
    """

    # Google Custom Search API Configuration
    google_api_key: str = Field(
        default="", description="Google Custom Search API key"
    )
    google_search_engine_id: str = Field(
        default="", description="Google Custom Search Engine ID"
    )
    google_api_base_url: str = Field(
        default="https://www.googleapis.com/customsearch/v1",
        description="Google Custom Search API base URL",
    )

    # Search Configuration
    default_max_results: int = Field(default=10, ge=1, le=100)
    default_language: str = Field(default="en")
    default_safe_search: bool = Field(default=True)
    search_timeout: float = Field(
        default=30.0, description="Search timeout in seconds"
    )

    # Rate Limiting
    requests_per_minute: int = Field(
        default=100, description="Max requests per minute"
    )
    requests_per_day: int = Field(
        default=10000, description="Max requests per day"
    )
    burst_limit: int = Field(default=10, description="Burst request limit")

    # Caching Configuration
    enable_cache: bool = Field(
        default=True, description="Enable search result caching"
    )
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    max_cache_size: int = Field(
        default=1000, description="Maximum cache entries"
    )
    cache_key_prefix: str = Field(
        default="websearch:", description="Cache key prefix"
    )

    # Performance Configuration
    max_concurrent_searches: int = Field(
        default=5, description="Max concurrent search requests"
    )
    connection_pool_size: int = Field(
        default=20, description="HTTP connection pool size"
    )
    retry_attempts: int = Field(
        default=3, description="Number of retry attempts"
    )
    retry_delay: float = Field(
        default=1.0, description="Delay between retries in seconds"
    )

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string",
    )
    enable_request_logging: bool = Field(
        default=True, description="Enable request logging"
    )

    # Security Configuration
    allowed_domains: Optional[List[str]] = Field(
        default=None,
        description="Allowed domains for search results (None = all allowed)",
    )
    blocked_domains: List[str] = Field(
        default_factory=list, description="Blocked domains for search results"
    )

    # Application Configuration
    app_name: str = Field(
        default="WebSearchTool", description="Application name"
    )
    app_version: str = Field(default="0.1.0", description="Application version")
    debug_mode: bool = Field(default=False, description="Enable debug mode")

    # Health Check Configuration
    health_check_interval: int = Field(
        default=300, description="Health check interval in seconds"
    )
    health_check_timeout: float = Field(
        default=10.0, description="Health check timeout in seconds"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("google_api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("Google API key cannot be empty")
        return v.strip()

    @field_validator("google_search_engine_id")
    @classmethod
    def validate_search_engine_id(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("Google Search Engine ID cannot be empty")
        return v.strip()

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()

    @field_validator("search_timeout")
    @classmethod
    def validate_timeout(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Search timeout must be positive")
        return v


settings = Settings()
