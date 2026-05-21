from __future__ import annotations

from dataclasses import dataclass
import json
import math
import re
import time
from typing import Protocol


def normalize_text(text: str) -> str:
    return " ".join(text.lower().split())


class EmbeddingClient(Protocol):
    def embed(self, text: str) -> list[float]: ...


class RedisHashClient(Protocol):
    def hset(self, name: str, key: str, value: str) -> None: ...
    def hgetall(self, name: str) -> dict[str, str]: ...


class FakeRedisHash:
    def __init__(self) -> None:
        self._storage: dict[str, dict[str, str]] = {}

    def hset(self, name: str, key: str, value: str) -> None:
        self._storage.setdefault(name, {})[key] = value

    def hgetall(self, name: str) -> dict[str, str]:
        return dict(self._storage.get(name, {}))


class SimpleEmbeddingClient:
    """Deterministic local embedding simulator for demos/tests."""

    def __init__(self, dimension: int = 16) -> None:
        self.dimension = dimension
        self._token_re = re.compile(r"[a-z0-9]+")

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        for token in self._token_re.findall(normalize_text(text)):
            index = hash(token) % self.dimension
            vector[index] += 1.0
        return vector


@dataclass
class CacheEntry:
    question: str
    response: str
    embedding: list[float]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class SemanticCache:
    def __init__(
        self,
        *,
        redis_client: RedisHashClient | None = None,
        embedding_client: EmbeddingClient | None = None,
        namespace: str = "semantic_cache",
        similarity_threshold: float = 0.82,
    ) -> None:
        self.redis_client = redis_client or FakeRedisHash()
        self.embedding_client = embedding_client or SimpleEmbeddingClient()
        self.namespace = namespace
        self.similarity_threshold = similarity_threshold

    def _serialize_entry(self, entry: CacheEntry) -> str:
        return json.dumps(
            {
                "question": entry.question,
                "response": entry.response,
                "embedding": entry.embedding,
            },
            ensure_ascii=True,
        )

    def _deserialize_entry(self, raw: str) -> CacheEntry:
        payload = json.loads(raw)
        return CacheEntry(
            question=str(payload["question"]),
            response=str(payload["response"]),
            embedding=[float(x) for x in payload["embedding"]],
        )

    def _load_all_entries(self) -> list[CacheEntry]:
        records = self.redis_client.hgetall(self.namespace)
        return [self._deserialize_entry(raw) for raw in records.values()]

    def check_cache(self, user_question: str) -> tuple[str | None, float]:
        # Embedding call for the incoming query.
        query_embedding = self.embedding_client.embed(user_question)

        best_score = -1.0
        best_response: str | None = None
        for entry in self._load_all_entries():
            score = cosine_similarity(query_embedding, entry.embedding)
            if score > best_score:
                best_score = score
                best_response = entry.response

        # Threshold gate for cache hit.
        if best_response is not None and best_score >= self.similarity_threshold:
            return best_response, best_score
        return None, best_score

    def store_response(self, user_question: str, response: str) -> None:
        normalized = normalize_text(user_question)
        embedding = self.embedding_client.embed(normalized)
        entry = CacheEntry(
            question=user_question,
            response=response,
            embedding=embedding,
        )
        # Redis hash structure: key(question) -> JSON payload with embedding + response.
        self.redis_client.hset(self.namespace, normalized, self._serialize_entry(entry))

    # Backward-compatible API used by existing supervisor flow.
    def get(self, key: str) -> str | None:
        response, _score = self.check_cache(key)
        return response

    def set(self, key: str, value: str) -> None:
        self.store_response(key, value)


def simulated_model_response(question: str, latency_ms: int = 680) -> str:
    time.sleep(latency_ms / 1000.0)
    return (
        "The statue likely represents a Roman river deity linked to civic protection and trade routes."
    )
