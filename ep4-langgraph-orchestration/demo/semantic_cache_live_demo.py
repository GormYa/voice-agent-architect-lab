from __future__ import annotations

from pathlib import Path
import sys
import time

sys.path.append(str(Path(__file__).resolve().parents[1]))

from graph.semantic_cache import (
    FakeRedisHash,
    SemanticCache,
    SimpleEmbeddingClient,
    simulated_model_response,
)


def run_question(cache: SemanticCache, question: str, threshold: float) -> None:
    started = time.perf_counter()
    cached, score = cache.check_cache(question)
    if cached is not None:
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        print(f"[CACHE HIT] score={score:.3f} threshold={threshold:.2f} latency={elapsed_ms:.1f}ms")
        print(f"Q: {question}")
        print(f"A: {cached}")
        print()
        return

    response = simulated_model_response(question)
    cache.store_response(question, response)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    print(f"[CACHE MISS] score={score:.3f} threshold={threshold:.2f} latency={elapsed_ms:.1f}ms")
    print(f"Q: {question}")
    print(f"A: {response}")
    print()


def main() -> None:
    threshold = 0.40
    cache = SemanticCache(
        redis_client=FakeRedisHash(),
        embedding_client=SimpleEmbeddingClient(),
        similarity_threshold=threshold,
    )
    questions = [
        "What does this Roman statue represent?",
        "Can you explain the meaning of this Roman statue?",
        "Who is this Roman figure meant to be?",
    ]
    seeded_response = (
        "The statue likely represents a Roman river deity linked to civic protection and trade routes."
    )
    cache.store_response("What does this Roman statue represent?", seeded_response)

    print("=== Semantic Cache Live Demo ===")
    print("Redis hash structure: normalized_question -> {question,response,embedding}")
    print("Cache pre-seeded with canonical Roman statue Q/A for slide demo.")
    print()
    for question in questions:
        run_question(cache, question, threshold)


if __name__ == "__main__":
    main()
