from __future__ import annotations


def cancel_echo(mic_frame: bytes, speaker_frame: bytes) -> bytes:
    # Lightweight placeholder: subtract mirrored bytes to emulate cancellation.
    out = bytearray()
    for i, b in enumerate(mic_frame):
        ref = speaker_frame[i] if i < len(speaker_frame) else 0
        out.append((b - ref) % 256)
    return bytes(out)
