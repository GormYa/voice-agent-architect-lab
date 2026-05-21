from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from graph.semantic_cache import (
    FakeRedisHash,
    SemanticCache,
    SimpleEmbeddingClient,
    cosine_similarity,
)


def test_cosine_similarity_basic() -> None:
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_check_cache_hits_similar_phrasing() -> None:
    cache = SemanticCache(
        redis_client=FakeRedisHash(),
        embedding_client=SimpleEmbeddingClient(),
        similarity_threshold=0.45,
    )
    cache.store_response(
        "What does this Roman statue represent?",
        "It represents a Roman river deity.",
    )

    result, score = cache.check_cache("Can you explain this Roman statue meaning?")
    assert result == "It represents a Roman river deity."
    assert score >= 0.45


def test_check_cache_miss_for_unrelated_question() -> None:
    cache = SemanticCache(
        redis_client=FakeRedisHash(),
        embedding_client=SimpleEmbeddingClient(),
        similarity_threshold=0.75,
    )
    cache.store_response("What does this Roman statue represent?", "River deity.")

    result, score = cache.check_cache("How do I reset my account password?")
    assert result is None
    assert score < 0.75
