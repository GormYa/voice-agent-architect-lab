from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from bridge.relay_session import build_relay_payload


def test_relay_payload():
    p = build_relay_payload("hello")
    assert p["type"] == "conversation_relay_session"
    assert p["prompt"] == "hello"
