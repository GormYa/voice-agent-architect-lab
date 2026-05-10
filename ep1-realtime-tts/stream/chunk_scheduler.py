from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any


@dataclass
class ChunkScheduler:
    schedule: list[int] = field(default_factory=lambda: [120, 160, 220, 300])
    idx: int = 0

    def next_chunk_chars(self) -> int:
        if self.idx < len(self.schedule) - 1:
            value = self.schedule[self.idx]
            self.idx += 1
            return value
        return self.schedule[-1]


def split_for_stream(text: str, scheduler: ChunkScheduler) -> list[str]:
    chunks: list[str] = []
    i = 0
    while i < len(text):
        size = scheduler.next_chunk_chars()
        chunks.append(text[i : i + size])
        i += size
    return chunks


def latency_ms(start: float) -> float:
    return (perf_counter() - start) * 1000
