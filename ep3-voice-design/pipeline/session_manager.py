from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SessionManager:
    active_voice_id: str | None = None
    voices: dict[str, dict] = field(default_factory=dict)

    def set_voice(self, name: str, persona: dict) -> str:
        voice_id = f"voice_{name}"
        self.voices[voice_id] = persona
        self.active_voice_id = voice_id
        return voice_id

    def get_active(self) -> dict | None:
        if not self.active_voice_id:
            return None
        return self.voices[self.active_voice_id]
