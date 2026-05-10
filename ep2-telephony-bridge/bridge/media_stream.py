from __future__ import annotations

import base64
import json

from .aec import cancel_echo
from .mu_law import mulaw_to_pcm16, pcm16_to_mulaw


def process_twilio_media_event(event_json: str, last_speaker_frame: bytes = b"") -> str:
    payload = json.loads(event_json)
    if payload.get("event") != "media":
        return json.dumps({"event": "ignored"})

    media_payload = payload["media"]["payload"]
    ulaw = base64.b64decode(media_payload)
    pcm = mulaw_to_pcm16(ulaw)
    cleaned = cancel_echo(pcm, last_speaker_frame)
    encoded = pcm16_to_mulaw(cleaned)

    return json.dumps({
        "event": "media",
        "media": {"payload": base64.b64encode(encoded).decode("ascii")},
    })


if __name__ == "__main__":
    print("Media stream module ready.")
