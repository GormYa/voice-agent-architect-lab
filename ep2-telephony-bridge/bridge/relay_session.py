from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RelayConfig:
    voice: str = "Rachel"
    interruption_sensitivity: str = "medium"
    digital_pause_ms: int = 120


def build_relay_payload(prompt: str, cfg: RelayConfig | None = None) -> dict:
    cfg = cfg or RelayConfig()
    return {
        "type": "conversation_relay_session",
        "voice": cfg.voice,
        "interruption_sensitivity": cfg.interruption_sensitivity,
        "digital_pause_ms": cfg.digital_pause_ms,
        "prompt": prompt,
    }
