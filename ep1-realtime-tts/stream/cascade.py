from __future__ import annotations

from time import perf_counter
from typing import AsyncIterator

from .chunk_scheduler import ChunkScheduler, latency_ms, split_for_stream


async def stream_cascade(user_text: str) -> AsyncIterator[dict]:
    start = perf_counter()
    # In production this stage is STT->LLM->TTS. Here we keep it deterministic and stream-safe.
    response_text = f"Agent reply: {user_text.strip()}"
    scheduler = ChunkScheduler()
    for idx, chunk in enumerate(split_for_stream(response_text, scheduler), start=1):
        yield {
            "type": "audio_chunk",
            "chunk_index": idx,
            "text_chunk": chunk,
            "latency_ms": round(latency_ms(start), 2),
            "flush": idx > 1 and chunk.endswith((".", "!", "?")),
        }
    yield {"type": "done", "total_latency_ms": round(latency_ms(start), 2)}
