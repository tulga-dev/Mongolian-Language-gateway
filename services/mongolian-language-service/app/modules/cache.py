from collections.abc import Awaitable, Callable
from hashlib import sha256


class MemoryCache:
    def __init__(self):
        self._values: dict[str, str] = {}

    def key(self, prefix: str, payload: str) -> str:
        digest = sha256(payload.encode("utf-8")).hexdigest()
        return f"{prefix}:{digest}"

    async def get_or_set(self, key: str, factory: Callable[[], Awaitable[str]]) -> str:
        if key not in self._values:
            self._values[key] = await factory()
        return self._values[key]


cache = MemoryCache()
