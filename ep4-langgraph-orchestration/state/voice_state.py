from __future__ import annotations

from typing import NotRequired, TypedDict


class TurnMessage(TypedDict):
    role: str
    content: str


class VoiceState(TypedDict):
    current_utterance: str
    turn_history: list[TurnMessage]
    active_task: str | None
    checkpoint_id: str
    in_flight_tts: list[str]
    intent: NotRequired[str]
    agent_response: NotRequired[str]
    interrupted: NotRequired[bool]


class RuntimeVoiceState(TypedDict):
    current_utterance: str
    turn_history: list[TurnMessage]
    active_task: str | None
    checkpoint_ref: str
    in_flight_tts: list[str]
    intent: NotRequired[str]
    agent_response: NotRequired[str]
    interrupted: NotRequired[bool]
