from __future__ import annotations

import asyncio
import json
import statistics

import websockets


async def run_once(uri: str, text: str) -> dict:
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"text": text}))
        while True:
            message = await ws.recv()
            event = json.loads(message)
            if event.get("type") == "done":
                return event


async def main() -> None:
    uri = "ws://127.0.0.1:8011/ws"
    prompts = [
        "Hello, this is a latency test.",
        "Please summarize last quarter returns in one sentence.",
        "How do I reduce response delay in voice agents?",
        "Give me a short warm greeting.",
        "What's the fastest path from transcript to audio?",
        "Explain chunk scheduling briefly.",
        "Tell me one tradeoff of flush true.",
        "How can I instrument first token latency?",
        "What does barge in mean in voice AI?",
        "Give me a 10-word closing line.",
    ]

    totals: list[float] = []
    first_audio: list[float] = []

    for p in prompts:
        done = await run_once(uri, p)
        totals.append(float(done["total_latency_ms"]))
        first_audio.append(float(done["timestamps_ms"]["first_audio_received"]))
        print(json.dumps(done))

    print("\n--- Percentiles (ms) ---")
    for label, values in (("total_latency", totals), ("final_transcript_to_first_audio", first_audio)):
        q = statistics.quantiles(values, n=100)
        print(f"{label}: p50={q[49]:.2f} p90={q[89]:.2f} p99={q[98]:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
