from __future__ import annotations

import audioop
from collections import deque


class AcousticEchoCanceller:
    """
    Minimal AEC primitive for demo/training use.
    - Keeps a short rolling reference buffer of speaker-output PCM frames.
    - Uses normalized cross-correlation to detect likely echo overlap.
    - Suppresses mic frame when correlation crosses threshold.
    """

    def __init__(self, threshold: float = 0.72, reference_frames: int = 6) -> None:
        self.threshold = threshold
        self.reference_buffer: deque[bytes] = deque(maxlen=reference_frames)

    def add_reference(self, speaker_frame_pcm16: bytes) -> None:
        if speaker_frame_pcm16:
            self.reference_buffer.append(speaker_frame_pcm16)

    def correlate(self, mic_frame_pcm16: bytes) -> float:
        if not self.reference_buffer or not mic_frame_pcm16:
            return 0.0

        # Correlate with most recent speaker reference frame.
        ref = self.reference_buffer[-1]
        n = min(len(mic_frame_pcm16), len(ref))
        if n < 4:
            return 0.0

        mic = mic_frame_pcm16[:n]
        spk = ref[:n]
        dot = audioop.mul(audioop.add(mic, b"\x00" * n, 2), 2, 1.0)
        # Reuse rms energy for stable normalization.
        mic_rms = max(audioop.rms(mic, 2), 1)
        spk_rms = max(audioop.rms(spk, 2), 1)
        # Quick overlap score via average absolute delta to the reference.
        diff = audioop.rms(audioop.add(mic, audioop.mul(spk, 2, -1.0), 2), 2)
        similarity = 1.0 - min(diff / max(mic_rms + spk_rms, 1), 1.0)
        _ = dot  # keep for readability while preserving lightweight implementation
        return max(0.0, min(similarity, 1.0))

    def should_suppress(self, mic_frame_pcm16: bytes) -> bool:
        return self.correlate(mic_frame_pcm16) >= self.threshold

    def suppress(self, mic_frame_pcm16: bytes) -> bytes:
        if self.should_suppress(mic_frame_pcm16):
            return b"\x00" * len(mic_frame_pcm16)
        return mic_frame_pcm16
