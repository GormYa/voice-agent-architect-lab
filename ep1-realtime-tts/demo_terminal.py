from __future__ import annotations

import asyncio
import json
import statistics

from stream.cascade import stream_cascade


async def run_once(text: str) -> dict:
    done = None
    async for event in stream_cascade(text):
        if event.get("type") == "done":
            done = event
    if done is None:
        raise RuntimeError("no done event returned")
    return done


async def main() -> None:
    prompts = [
        "hello",
        "summarize media trends",
        "explain low latency tts",
        "give a short greeting",
        "what is chunk schedule",
        "how to force flush",
        "measure first token timing",
        "what is barge in",
        "close with one sentence",
        "final sample",
    ]
    totals: list[float] = []
    first_audio: list[float] = []

    for p in prompts:
        done = await run_once(p)
        totals.append(float(done["total_latency_ms"]))
        first_audio.append(float(done["timestamps_ms"]["first_audio_received"]))
        print(json.dumps(done))

    print("\n--- Percentiles (ms) ---")
    q_total = statistics.quantiles(totals, n=100)
    q_audio = statistics.quantiles(first_audio, n=100)
    print(f"total_latency_ms: p50={q_total[49]:.2f} p90={q_total[89]:.2f} p99={q_total[98]:.2f}")
    print(f"final_transcript_to_first_audio_ms: p50={q_audio[49]:.2f} p90={q_audio[89]:.2f} p99={q_audio[98]:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
