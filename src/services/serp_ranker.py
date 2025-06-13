import json
from typing import Any, Dict, List

from ..core.exceptions import LLMException
from ..core.interfaces import LLMInterface  # Remove duplicate import
from ..utils.logging import logger


class SERPRanker:
    """
    Uses an LLM to assign 0-10 relevance scores to each SERP item.
    """

    def __init__(self, llm: LLMInterface, top_k: int = 3) -> None:
        super().__init__()  # Call parent constructor
        self.llm = llm
        self.top_k = top_k

    async def rank(
        self, query: str, serp_json: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        if "items" not in serp_json or not serp_json["items"]:
            return []

        prompt = self._build_prompt(query, serp_json["items"])
        try:
            raw = await self.llm.complete(prompt)
            scores = json.loads(raw)
            print("x" * 100)
            print(raw)
            print("-" * 100)
            print(scores)
            print("x" * 100)
        except (json.JSONDecodeError, LLMException) as e:
            logger.error(
                "SERP ranking failed – falling back to first k", error=str(e)
            )
            # Fallback: keep the first k results unchanged
            return serp_json["items"][: self.top_k]
        # attach score & sort
        for obj in scores:
            idx = int(obj["index"]) - 1  # 1-based index in the prompt
            if 0 <= idx < len(serp_json["items"]):
                serp_json["items"][idx]["serp_score"] = float(obj["score"])

        ranked = sorted(
            serp_json["items"],
            key=lambda x: x.get("serp_score", -1.0),
            reverse=True,
        )
        return ranked[: self.top_k]

    def _build_prompt(self, query: str, items: List[Dict[str, Any]]) -> str:
        lines = [
            "You are an expert search analyst.",
            (
                "For EACH Google result below, provide a brutal honesty relevance"
                " score from 0 (irrelevant) to 10 (perfectly on-topic)."
            ),  # Fix implicit concatenation
            (
                "Return ONLY valid JSON: a list of objects "
                'like {"index": 1, "score": 7}.'
            ),  # Fix implicit concatenation
            f"User query: {query}",
            "Results:",
        ]
        for i, it in enumerate(items, 1):
            title = it.get("title", "")
            snippet = it.get("snippet", "")
            url = it.get("link", "")
            lines.append(f"{i}. {title}\nURL: {url}\nSnippet: {snippet}")
        return "\n".join(lines)
