from typing import Any, Dict, Optional

import aiohttp

from ..config.settings import settings
from ..core.exceptions import APIRequestException
from ..utils.logging import logger


class GoogleCSEClient:
    BASE_URL = "https://www.googleapis.com/customsearch/v1"

    async def fetch(
        self, query: str, num_results: int = settings.default_num_results
    ) -> Optional[Dict[Any, Any]]:
        params = {
            "key": settings.google_api_key,
            "cx": settings.google_cse_id,
            "q": query,
            "num": min(num_results, 10),
        }

        timeout = aiohttp.ClientTimeout(total=settings.http_timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.get(self.BASE_URL, params=params) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    logger.info(
                        "Google CSE request >> OK",
                        status=resp.status,
                        query=query,
                        results=len(data.get("items", [])),
                    )
                    return data
            except Exception as e:
                logger.error(
                    "Google CSE request failed", error=str(e), query=query
                )
                raise APIRequestException(str(e)) from e
