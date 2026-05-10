from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InMemoryCheckpointer:
    store: dict[int, dict]

    def save(self, turn_id: int, state: dict) -> None:
        self.store[turn_id] = dict(state)

    def load(self, turn_id: int) -> dict | None:
        return self.store.get(turn_id)
