from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any

import redis
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver


@dataclass
class InMemoryCheckpointer:
    store: dict[int, dict]

    def save(self, turn_id: int, state: dict) -> None:
        self.store[turn_id] = dict(state)

    def load(self, turn_id: int) -> dict | None:
        return self.store.get(turn_id)


@dataclass
class RedisCheckpointer(BaseCheckpointSaver):
    redis_client: Any
    key_prefix: str = "voice_state"
    ttl_seconds: int = 3600
    _fallback: InMemorySaver = field(default_factory=InMemorySaver)

    @classmethod
    def from_url(
        cls,
        redis_url: str,
        *,
        key_prefix: str = "voice_state",
        ttl_seconds: int = 3600,
    ) -> "RedisCheckpointer":
        client = redis.Redis.from_url(redis_url, decode_responses=True)
        return cls(client, key_prefix=key_prefix, ttl_seconds=ttl_seconds)

    # LangGraph-compatible methods (delegate core protocol to in-memory saver)
    def get_tuple(self, config):
        return self._fallback.get_tuple(config)

    def list(self, config, *, filter=None, before=None, limit=None):
        return self._fallback.list(config, filter=filter, before=before, limit=limit)

    def put_writes(self, config, writes, task_id, task_path=""):
        return self._fallback.put_writes(config, writes, task_id, task_path)

    def get_next_version(self, current, channel):
        return self._fallback.get_next_version(current, channel)

    def put(self, *args, **kwargs):  # type: ignore[override]
        if len(args) == 3 and isinstance(args[0], str):
            thread_id, checkpoint_id, state = args
            return self._put_state(thread_id, checkpoint_id, state)
        return self._fallback.put(*args, **kwargs)

    def get(self, *args, **kwargs):  # type: ignore[override]
        if len(args) == 2 and isinstance(args[0], str):
            thread_id, checkpoint_id = args
            return self._get_state(thread_id, checkpoint_id)
        return self._fallback.get(*args, **kwargs)

    def _put_state(self, thread_id: str, checkpoint_id: str, state: dict[str, Any]) -> None:
        key = self._state_key(thread_id)
        payload = json.dumps(state)
        self.redis_client.hset(key, checkpoint_id, payload)
        self.redis_client.expire(key, self.ttl_seconds)

    def _get_state(self, thread_id: str, checkpoint_id: str) -> dict[str, Any] | None:
        key = self._state_key(thread_id)
        raw = self.redis_client.hget(key, checkpoint_id)
        if raw is None:
            return None
        return json.loads(raw)

    def _state_key(self, thread_id: str) -> str:
        return f"{self.key_prefix}:{thread_id}"
