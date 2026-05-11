from __future__ import annotations

from time import perf_counter
from typing import AsyncIterator

from .chunk_scheduler import ChunkScheduler, latency_ms, split_for_stream


async def stream_cascade(user_text: str) -> AsyncIterator[dict]:
    start = perf_counter()
    final_transcript_ts_ms = round(latency_ms(start), 2)
    # In production this stage is STT->LLM->TTS. Here we keep it deterministic and stream-safe.
    response_text = f"Agent reply: {user_text.strip()}"
    scheduler = ChunkScheduler()
    chunks = split_for_stream(response_text, scheduler)
    first_token_received_ts_ms = round(latency_ms(start), 2)
    first_audio_received_ts_ms: float | None = None

    for idx, chunk in enumerate(chunks, start=1):
        if first_audio_received_ts_ms is None:
            first_audio_received_ts_ms = round(latency_ms(start), 2)
        yield {
            "type": "audio_chunk",
            "chunk_index": idx,
            "text_chunk": chunk,
            "latency_ms": round(latency_ms(start), 2),
            "flush": idx > 1 and chunk.endswith((".", "!", "?")),
        }
    yield {
        "type": "done",
        "total_latency_ms": round(latency_ms(start), 2),
        "timestamps_ms": {
            "final_transcript": final_transcript_ts_ms,
            "first_token_received": first_token_received_ts_ms,
            "first_audio_received": first_audio_received_ts_ms,
        },
        "breakdown_ms": {
            "stt_to_first_token": round(first_token_received_ts_ms - final_transcript_ts_ms, 2),
            "first_token_to_first_audio": round((first_audio_received_ts_ms or 0.0) - first_token_received_ts_ms, 2),
            "final_transcript_to_first_audio": round((first_audio_received_ts_ms or 0.0) - final_transcript_ts_ms, 2),
        },
    }
