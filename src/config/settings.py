from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings.main import SettingsConfigDict


class Settings(BaseSettings):
    """
    Global configuration loaded from environment variables or .env
    """

    google_api_key: str = Field(
        default="", description="API key for google search engine"
    )
    google_case_id: str = Field(
        default="", description="Google Search Engine ID"
    )
    default_num_results: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Number of results to be returned from the google search api",
    )

    # HTTP
    http_timeout: float = Field(default=10.0)
    retry_backoff: float = Field(default=0.5)

    # Caching
    enable_cache: bool = Field(default=True)
    max_cache_size: int = Field(default=128)

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
