from __future__ import annotations


class AgentMemory:
    def __init__(self) -> None:
        self._items: list[str] = []

    def add(self, item: str) -> None:
        if item:
            self._items.append(item)

    def items(self) -> list[str]:
        return list(self._items)
