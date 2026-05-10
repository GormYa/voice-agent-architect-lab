from __future__ import annotations


class SemanticCache:
    def __init__(self) -> None:
        self._items: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self._items.get(key.lower().strip())

    def set(self, key: str, value: str) -> None:
        self._items[key.lower().strip()] = value
