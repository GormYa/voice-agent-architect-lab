from __future__ import annotations

from struct import iter_unpack, pack


def pcm16_to_mulaw(pcm_bytes: bytes, sample_width: int = 2) -> bytes:
    if sample_width != 2:
        raise ValueError("Only 16-bit PCM is supported in this demo implementation.")
    out = bytearray()
    for (sample,) in iter_unpack("<h", pcm_bytes):
        out.append(_linear2ulaw(sample))
    return bytes(out)


def mulaw_to_pcm16(mulaw_bytes: bytes, sample_width: int = 2) -> bytes:
    if sample_width != 2:
        raise ValueError("Only 16-bit PCM is supported in this demo implementation.")
    out = bytearray()
    for b in mulaw_bytes:
        out.extend(pack("<h", _ulaw2linear(b)))
    return bytes(out)


_BIAS = 0x84
_CLIP = 32635


def _linear2ulaw(sample: int) -> int:
    sign = 0x80 if sample < 0 else 0
    if sample < 0:
        sample = -sample
    if sample > _CLIP:
        sample = _CLIP
    sample = sample + _BIAS

    exponent = 7
    exp_mask = 0x4000
    while exponent > 0 and (sample & exp_mask) == 0:
        exponent -= 1
        exp_mask >>= 1

    mantissa = (sample >> (exponent + 3)) & 0x0F
    ulaw = ~(sign | (exponent << 4) | mantissa) & 0xFF
    return ulaw


def _ulaw2linear(ulaw_byte: int) -> int:
    u = ~ulaw_byte & 0xFF
    sign = u & 0x80
    exponent = (u >> 4) & 0x07
    mantissa = u & 0x0F
    sample = ((mantissa << 3) + _BIAS) << exponent
    sample -= _BIAS
    return -sample if sign else sample
