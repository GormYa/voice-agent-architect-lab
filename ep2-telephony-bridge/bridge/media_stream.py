from __future__ import annotations

import base64
import os
import json

from .aec import AcousticEchoCanceller
from .mu_law import mulaw_to_pcm16, pcm16_to_mulaw


AEC = AcousticEchoCanceller()


def feed_stt(frame_pcm16: bytes, corr: float, suppressed: bool) -> str:
    """
    Placeholder STT stage for architecture demo.
    In production: send frame_pcm16 to your streaming STT engine.
    """
    if not frame_pcm16 or set(frame_pcm16) == {0}:
        return ""
    if corr > 0.7 and not suppressed:
        return "i need help help help"
    if suppressed:
        return "i need help"
    return "recognized_user_audio"


def process_twilio_media_event(event_json: str, last_speaker_frame: bytes = b"") -> str:
    aec_enabled = os.getenv("AEC_ENABLED", "1") == "1"
    payload = json.loads(event_json)
    if payload.get("event") != "media":
        return json.dumps({"event": "ignored"})

    media_payload = payload["media"]["payload"]
    # 1) Twilio 8kHz mu-law payload -> PCM16
    ulaw = base64.b64decode(media_payload)
    pcm = mulaw_to_pcm16(ulaw)

    # 2) AEC sits here: after decode, before STT feed
    cleaned = pcm
    corr = 0.0
    suppressed = False
    if aec_enabled:
        if last_speaker_frame:
            AEC.add_reference(last_speaker_frame)
        corr = AEC.correlate(pcm)
        suppressed = AEC.should_suppress(pcm)
        cleaned = AEC.suppress(pcm)

    # 3) STT consumes echo-reduced frame
    stt_text = feed_stt(cleaned, corr=corr, suppressed=suppressed)
    encoded = pcm16_to_mulaw(cleaned)

    return json.dumps({
        "event": "media",
        "media": {"payload": base64.b64encode(encoded).decode("ascii")},
        "debug": {
            "aec_enabled": aec_enabled,
            "correlation": round(corr, 3),
            "suppressed": suppressed,
            "stt_text": stt_text,
        },
    })


if __name__ == "__main__":
    print("Media stream module ready.")
