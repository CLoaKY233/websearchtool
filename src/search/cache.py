import hashlib
from collections import OrderedDict
from typing import Any, Dict

from src.core.exceptions import CacheMissException

from ..config.settings import settings


class LRUCache:
    """Very small thread safe LRU cache"""

    def __init__(self, max_size: int = settings.max_cache_size):
        super().__init__()
        self.max_size = max_size
        self._data: OrderedDict[str, Dict[str, Any]] = OrderedDict()

    def _hash(self, query: str) -> str:
        return hashlib.md5(query.lower().strip().encode()).hexdigest()

    def get(self, query: str) -> Dict[str, Any]:
        h = self._hash(query)
        try:
            value = self._data.pop(h)
            self._data[h] = value
            return value
        except KeyError:
            raise CacheMissException

    def put(self, query: str, value: Dict[str, Any]) -> None:
        h = self._hash(query)
        if h in self._data:
            self._data.pop(h)
        elif len(self._data) >= self.max_size:
            self._data.popitem(last=False)
        self._data[h] = value
