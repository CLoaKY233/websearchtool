from typing import Any, AsyncIterator

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import UserMessage
from azure.core.credentials import AzureKeyCredential

from ..config.settings import settings
from ..core.exceptions import LLMException
from ..core.interfaces import LLMInterface, StreamingChunk
from ..utils.logging import logger


class GitHubLLM(LLMInterface):
    """Thin wrapper around GitHub-hosted models (azure.ai.inference)"""

    def __init__(self) -> None:
        super().__init__()
        try:
            self._client = ChatCompletionsClient(
                endpoint="https://models.github.ai/inference",
                credential=AzureKeyCredential(settings.github_token),
            )
        except Exception as e:
            logger.error("GitHub LLM init failed", error=str(e))
            raise LLMException(str(e))

    # ---------- single completion ------------------------------------
    async def complete(self, prompt: str, **kwargs: Any) -> str:
        try:
            resp = self._client.complete(
                messages=[UserMessage(prompt)],
                model=kwargs.get("model", settings.llm_model),
                temperature=kwargs.get("temperature", settings.llm_temperature),
                max_tokens=kwargs.get("max_tokens", settings.llm_max_tokens),
                top_p=1.0,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.error("LLM completion failed", error=str(e))
            raise LLMException(str(e))

    # ---------- streaming completion ---------------------------------
    async def stream(
        self, prompt: str, **kwargs: Any
    ) -> AsyncIterator[StreamingChunk]:
        try:
            response = self._client.complete(
                stream=True,
                messages=[UserMessage(prompt)],
                model=kwargs.get("model", settings.llm_model),
                temperature=kwargs.get("temperature", settings.llm_temperature),
                max_tokens=kwargs.get("max_tokens", settings.llm_max_tokens),
                top_p=1.0,
                model_extras={"stream_options": {"include_usage": True}},
            )
            for delta in response:
                chunk = delta.choices[0].delta.content or ""
                done = bool(delta.usage)
                yield StreamingChunk(
                    content=chunk,
                    is_complete=done,
                    usage_info=getattr(delta, "usage", None),
                )
        except Exception as e:
            logger.error("LLM streaming failed", error=str(e))
            raise LLMException(str(e))
