from __future__ import annotations


def detect_barge_in(user_audio_energy: float, threshold: float = 0.6) -> bool:
    return user_audio_energy >= threshold


def rollback_to_checkpoint(checkpoint: dict | None, current: dict) -> dict:
    if checkpoint is None:
        return current
    merged = dict(checkpoint)
    merged["interrupted"] = True
    return merged
