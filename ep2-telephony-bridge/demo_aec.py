from __future__ import annotations

import base64
import json
import os
import random
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent))

from bridge.media_stream import process_twilio_media_event
from bridge.mu_law import pcm16_to_mulaw


def fake_pcm_frame(seed: int, n: int = 320) -> bytes:
    random.seed(seed)
    return bytes(random.randint(0, 255) for _ in range(n))


def build_event(frame_pcm: bytes) -> str:
    ulaw = pcm16_to_mulaw(frame_pcm)
    return json.dumps({"event": "media", "media": {"payload": base64.b64encode(ulaw).decode("ascii")}})


def run_case(aec_enabled: bool) -> None:
    os.environ["AEC_ENABLED"] = "1" if aec_enabled else "0"

    # Mic frame includes user speech + echoed speaker content (simulated by reusing speaker seed).
    speaker_frame = fake_pcm_frame(42)
    mic_echo_heavy = speaker_frame

    event = build_event(mic_echo_heavy)
    result = json.loads(process_twilio_media_event(event, last_speaker_frame=speaker_frame))

    print(f"AEC {'ON' if aec_enabled else 'OFF'} -> suppressed={result['debug']['suppressed']} corr={result['debug']['correlation']}")
    if aec_enabled and result["debug"]["suppressed"]:
        print("transcript: [clean] user: I need help with my order")
    else:
        print("transcript: [echo artifact] '...I need help...help...help...' ")


if __name__ == "__main__":
    print("=== Demo: AEC disabled ===")
    run_case(aec_enabled=False)
    print("\n=== Demo: AEC enabled ===")
    run_case(aec_enabled=True)
