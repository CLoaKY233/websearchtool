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
    google_cse_id: str = Field(
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

    # Github Models settings
    github_token: str = Field(
        default="", description="GitHub Models auth token"
    )
    llm_model: str = Field(
        default="meta/Meta-Llama-3.1-70B-Instruct",
        description="Default model for SERP ranking",
    )
    llm_temperature: float = Field(default=0.0, ge=0.0, le=1.0)
    llm_max_tokens: int = Field(default=1024, ge=256, le=4096)


settings = Settings()
