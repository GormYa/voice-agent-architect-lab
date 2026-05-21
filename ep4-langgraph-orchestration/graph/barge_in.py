from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from state.voice_state import VoiceState


class BargeInDetected(RuntimeError):
    pass


class TTSController(Protocol):
    def stop(self) -> None: ...
    def cancel(self, tts_id: str) -> None: ...


@dataclass
class AudioWindow:
    tts_start_ms: int
    tts_end_ms: int


def detect_barge_in(user_audio_energy: float, threshold: float = 0.6) -> bool:
    return user_audio_energy >= threshold


def handle_user_audio_event(
    *,
    user_audio_timestamp_ms: int,
    tts_window: AudioWindow,
    user_audio_energy: float,
    energy_threshold: float = 0.6,
) -> None:
    # Barge-in only applies while TTS is actively speaking.
    overlaps_tts = tts_window.tts_start_ms <= user_audio_timestamp_ms <= tts_window.tts_end_ms
    if overlaps_tts and detect_barge_in(user_audio_energy, energy_threshold):
        raise BargeInDetected(
            f"User speech at {user_audio_timestamp_ms}ms interrupted active TTS window "
            f"{tts_window.tts_start_ms}-{tts_window.tts_end_ms}ms."
        )


def rollback_to_checkpoint(checkpoint: dict | None, current: dict) -> dict:
    if checkpoint is None:
        return current
    merged = dict(checkpoint)
    merged["interrupted"] = True
    return merged


def perform_barge_in_rollback(
    *,
    tts_controller: TTSController,
    redis_checkpointer,
    thread_id: str,
    checkpoint_id: str,
    current_state: VoiceState,
    interruption_utterance: str,
) -> VoiceState:
    # Step 1: stop current TTS stream immediately.
    tts_controller.stop()
    # Cancellation logic: cancel all speculative chunks still in-flight.
    for tts_id in current_state.get("in_flight_tts", []):
        tts_controller.cancel(tts_id)
    # Step 2: fetch latest checkpointed state.
    checkpoint = redis_checkpointer.get(thread_id, checkpoint_id)
    restored = rollback_to_checkpoint(checkpoint, current_state)
    # Step 3: inject interruption context and route with updated utterance.
    restored_state: VoiceState = {
        **restored,
        "current_utterance": interruption_utterance,
        "active_task": None,
        "checkpoint_id": checkpoint_id,
        "in_flight_tts": [],
        "interrupted": True,
    }
    return restored_state


def resume_from_redis_checkpoint(
    *,
    graph,
    redis_checkpointer,
    thread_id: str,
    checkpoint_id: str,
    fallback_state: VoiceState,
) -> VoiceState:
    restored = redis_checkpointer.get(thread_id, checkpoint_id)
    if restored is None:
        return graph.invoke(fallback_state)

    restored_state: VoiceState = {**restored, "interrupted": True}
    return graph.invoke(restored_state)
