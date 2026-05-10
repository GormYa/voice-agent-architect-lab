from __future__ import annotations

from typing import TypedDict


class VoiceState(TypedDict):
    user_text: str
    current_response: str
    interrupted: bool
    turn_id: int
