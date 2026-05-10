from __future__ import annotations

import audioop


def pcm16_to_mulaw(pcm_bytes: bytes, sample_width: int = 2) -> bytes:
    return audioop.lin2ulaw(pcm_bytes, sample_width)


def mulaw_to_pcm16(mulaw_bytes: bytes, sample_width: int = 2) -> bytes:
    return audioop.ulaw2lin(mulaw_bytes, sample_width)
