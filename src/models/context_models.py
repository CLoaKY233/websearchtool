from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PassageContext(BaseModel):
    """Individual passage context from a crawled page"""

    url: str = Field(description="Source Url")
    passage: str = Field(description="Extracted text passage")
    score: float = Field(description="Relevance score")
    position: int = Field(description="Position in the page")


class ContextResponse(BaseModel):
    """Final context response for LLM consumption"""

    query: str = Field(description="Original search query")
    contexts: List[PassageContext] = Field(description="Extracted contexts")
    metadata: Dict[str, Any] = Field(description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.now)


class SERPItem(BaseModel):
    """Enhanced SERP item with scoring"""

    title: str
    link: str
    snippet: str
    tfidf_score: float = 0.0
    bmm25_score: float = 0.0
    llm_score: float = 0.0
    final_score: float = 0.0


class CrawlResult(BaseModel):
    """Result from crawling a single URL"""

    url: str
    success: bool
    content: str = ""
    error: Optional[str] = None
    content_type: Optional[str] = None
    size_bytes: int = 0
