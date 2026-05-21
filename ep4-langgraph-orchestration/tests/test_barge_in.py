from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from graph.barge_in import (
    AudioWindow,
    BargeInDetected,
    detect_barge_in,
    handle_user_audio_event,
    perform_barge_in_rollback,
)
from state.redis_checkpointer import RedisCheckpointer
from state.voice_state import VoiceState


def test_barge_in_threshold():
    assert detect_barge_in(0.7)
    assert not detect_barge_in(0.5)


def test_timestamp_overlap_raises_barge_in_detected():
    try:
        handle_user_audio_event(
            user_audio_timestamp_ms=1200,
            tts_window=AudioWindow(tts_start_ms=1000, tts_end_ms=2500),
            user_audio_energy=0.8,
        )
    except BargeInDetected:
        return
    assert False, "Expected BargeInDetected for overlapping user speech"


def test_three_step_rollback_stops_tts_gets_checkpoint_and_injects_context():
    class FakeTTS:
        def __init__(self):
            self.stopped = False
            self.cancelled = []

        def stop(self):
            self.stopped = True

        def cancel(self, tts_id: str):
            self.cancelled.append(tts_id)

    class FakeRedis:
        def __init__(self):
            self.hashes = {}

        def hset(self, key, field, value):
            self.hashes.setdefault(key, {})[field] = value
            return 1

        def hget(self, key, field):
            return self.hashes.get(key, {}).get(field)

        def expire(self, key, ttl):
            return True

    current: VoiceState = {
        "current_utterance": "Original long answer from the agent.",
        "turn_history": [],
        "active_task": "general_agent",
        "checkpoint_id": "turn-7",
        "in_flight_tts": ["tts-1", "tts-2"],
    }
    checkpoint: VoiceState = {
        "current_utterance": "Checkpointed answer state.",
        "turn_history": [{"role": "assistant", "content": "Checkpointed answer state."}],
        "active_task": "general_agent",
        "checkpoint_id": "turn-7",
        "in_flight_tts": ["tts-1", "tts-2"],
    }
    fake_tts = FakeTTS()
    cp = RedisCheckpointer(FakeRedis())
    cp.put("voice-thread", "turn-7", checkpoint)

    rolled = perform_barge_in_rollback(
        tts_controller=fake_tts,
        redis_checkpointer=cp,
        thread_id="voice-thread",
        checkpoint_id="turn-7",
        current_state=current,
        interruption_utterance="Wait, can you explain that more simply?",
    )

    assert fake_tts.stopped is True
    assert fake_tts.cancelled == ["tts-1", "tts-2"]
    assert rolled["current_utterance"] == "Wait, can you explain that more simply?"
    assert rolled["checkpoint_id"] == "turn-7"
    assert rolled["interrupted"] is True
    assert rolled["active_task"] is None
    assert rolled["in_flight_tts"] == []
