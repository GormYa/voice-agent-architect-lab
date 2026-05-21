from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from graph.barge_in import resume_from_redis_checkpoint
from graph.supervisor import build_graph
from state.redis_checkpointer import RedisCheckpointer
from state.voice_state import VoiceState


class FakeRedis:
    def __init__(self):
        self.hashes = {}
        self.ttl = {}

    def hset(self, key, field, value):
        self.hashes.setdefault(key, {})[field] = value
        return 1

    def hget(self, key, field):
        return self.hashes.get(key, {}).get(field)

    def expire(self, key, ttl_seconds):
        self.ttl[key] = ttl_seconds
        return True


def _demo_state() -> VoiceState:
    return {
        "current_utterance": "Can you book a demo for tomorrow?",
        "turn_history": [],
        "active_task": None,
        "checkpoint_id": "turn-1",
        "in_flight_tts": [],
    }


def test_redis_put_get_uses_hset_hget_and_ttl():
    fake = FakeRedis()
    cp = RedisCheckpointer(fake, key_prefix="voice_state", ttl_seconds=120)
    state = _demo_state()

    cp.put("thread-1", "turn-1", state)
    restored = cp.get("thread-1", "turn-1")

    assert restored == state
    assert fake.ttl["voice_state:thread-1"] == 120


def test_graph_compiles_with_checkpointer_attached():
    fake = FakeRedis()
    cp = RedisCheckpointer(fake)
    graph = build_graph(checkpointer=cp)

    result = graph.invoke(_demo_state())
    assert result["active_task"] == "booking_agent"
    assert result["intent"] == "booking"


def test_resume_from_redis_checkpoint_reads_state_and_resumes_graph():
    fake = FakeRedis()
    cp = RedisCheckpointer(fake)
    graph = build_graph(checkpointer=cp)
    checkpoint_state: VoiceState = {
        "current_utterance": "My audio is broken and latency is high.",
        "turn_history": [],
        "active_task": "support_agent",
        "checkpoint_id": "turn-5",
        "in_flight_tts": [],
    }
    cp.put("thread-9", "turn-5", checkpoint_state)

    resumed = resume_from_redis_checkpoint(
        graph=graph,
        redis_checkpointer=cp,
        thread_id="thread-9",
        checkpoint_id="turn-5",
        fallback_state=_demo_state(),
    )

    assert resumed["interrupted"] is True
    assert resumed["intent"] == "technical_support"
    assert resumed["active_task"] == "support_agent"
