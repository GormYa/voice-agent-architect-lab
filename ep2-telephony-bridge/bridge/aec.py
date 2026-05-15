from __future__ import annotations

from collections import deque
from math import sqrt
from struct import iter_unpack


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
        mic_samples = [s[0] for s in iter_unpack("<h", mic)]
        spk_samples = [s[0] for s in iter_unpack("<h", spk)]
        if not mic_samples or not spk_samples:
            return 0.0

        mic_rms = max(sqrt(sum(v * v for v in mic_samples) / len(mic_samples)), 1.0)
        spk_rms = max(sqrt(sum(v * v for v in spk_samples) / len(spk_samples)), 1.0)
        diffs = [a - b for a, b in zip(mic_samples, spk_samples)]
        diff_rms = sqrt(sum(v * v for v in diffs) / len(diffs))
        similarity = 1.0 - min(diff_rms / max(mic_rms + spk_rms, 1.0), 1.0)
        return max(0.0, min(similarity, 1.0))

    def should_suppress(self, mic_frame_pcm16: bytes) -> bool:
        return self.correlate(mic_frame_pcm16) >= self.threshold

    def suppress(self, mic_frame_pcm16: bytes) -> bytes:
        if self.should_suppress(mic_frame_pcm16):
            return b"\x00" * len(mic_frame_pcm16)
        return mic_frame_pcm16
