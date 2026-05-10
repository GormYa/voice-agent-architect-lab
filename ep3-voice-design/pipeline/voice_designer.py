from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VoicePersona:
    description: str
    accent: str
    timbre: str


def build_voice_persona(label: str, era: str, mood: str) -> VoicePersona:
    description = f"{mood} {era} {label} narrator"
    accent = "neutral"
    timbre = "warm" if mood in {"calm", "friendly"} else "bright"
    return VoicePersona(description=description, accent=accent, timbre=timbre)
