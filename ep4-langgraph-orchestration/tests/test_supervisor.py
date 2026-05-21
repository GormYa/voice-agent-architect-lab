from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from graph.supervisor import (
    Supervisor,
    build_graph,
    handle_turn,
    route_after_supervisor,
)
from graph.semantic_cache import SemanticCache
from state.redis_checkpointer import InMemoryCheckpointer
from state.voice_state import VoiceState


def test_supervisor_routes_booking_intent():
    state: VoiceState = {
        "current_utterance": "Can you book a demo for tomorrow?",
        "turn_history": [],
        "active_task": None,
        "checkpoint_id": "turn-1",
        "in_flight_tts": [],
    }

    next_state = Supervisor().invoke(state)

    assert next_state["intent"] == "booking"
    assert next_state["active_task"] == "booking_agent"
    assert route_after_supervisor(next_state) == "booking_agent"


def test_graph_invokes_sub_agent_from_supervisor_route():
    graph = build_graph()
    state: VoiceState = {
        "current_utterance": "Can you troubleshoot my audio latency?",
        "turn_history": [],
        "active_task": None,
        "checkpoint_id": "turn-2",
        "in_flight_tts": [],
    }

    result = graph.invoke(state)

    assert result["intent"] == "technical_support"
    assert result["active_task"] == "support_agent"
    assert result["agent_response"].startswith("Support agent:")
    assert result["turn_history"]


def test_handle_turn_keeps_existing_cache_checkpoint_flow():
    cache = SemanticCache()
    checkpointer = InMemoryCheckpointer(store={})

    first = handle_turn("book a demo", 1, cache, checkpointer)
    second = handle_turn("book a demo", 2, cache, checkpointer)

    assert first["current_response"] == second["current_response"]
    assert checkpointer.load(1)["current_response"] == first["current_response"]
    assert checkpointer.load(2)["current_response"] == second["current_response"]
