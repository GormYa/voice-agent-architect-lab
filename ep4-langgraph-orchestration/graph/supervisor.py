from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Literal

sys.path.append(str(Path(__file__).resolve().parents[1]))

from langgraph.graph import END, StateGraph

from graph.semantic_cache import SemanticCache
from graph.speculative import speculative_response
from state.redis_checkpointer import InMemoryCheckpointer, RedisCheckpointer
from state.voice_state import RuntimeVoiceState, TurnMessage, VoiceState


Intent = Literal["booking", "technical_support", "billing", "general"]

INTENT_TO_AGENT: dict[Intent, str] = {
    "booking": "booking_agent",
    "technical_support": "support_agent",
    "billing": "billing_agent",
    "general": "general_agent",
}


@dataclass
class Supervisor:
    """Supervisor node: classify intent, then annotate state for graph routing."""

    def invoke(self, state: VoiceState | RuntimeVoiceState) -> VoiceState | RuntimeVoiceState:
        utterance = state["current_utterance"]
        intent = classify_intent(utterance)
        next_state = {
            **state,
            "intent": intent,
            "active_task": INTENT_TO_AGENT[intent],
        }
        return next_state


def classify_intent(utterance: str) -> Intent:
    text = utterance.lower()
    if any(word in text for word in ("book", "schedule", "appointment", "demo")):
        return "booking"
    if any(word in text for word in ("latency", "audio", "bug", "broken", "error", "troubleshoot")):
        return "technical_support"
    if any(word in text for word in ("invoice", "billing", "charge", "payment", "refund")):
        return "billing"
    return "general"


def route_after_supervisor(state: VoiceState | RuntimeVoiceState) -> str:
    return state["active_task"] or "general_agent"


def booking_agent(state: RuntimeVoiceState) -> RuntimeVoiceState:
    return _append_agent_response(
        state,
        "Booking agent: I can collect the preferred date, time, and attendee details.",
    )


def support_agent(state: RuntimeVoiceState) -> RuntimeVoiceState:
    return _append_agent_response(
        state,
        "Support agent: I will inspect the audio path, latency budget, and recent errors.",
    )


def billing_agent(state: RuntimeVoiceState) -> RuntimeVoiceState:
    return _append_agent_response(
        state,
        "Billing agent: I can review the subscription, invoice, and payment status.",
    )


def general_agent(state: RuntimeVoiceState) -> RuntimeVoiceState:
    return _append_agent_response(
        state,
        "General agent: I can answer the question directly or route to a specialist.",
    )


def build_graph(checkpointer: RedisCheckpointer | None = None):
    graph = StateGraph(RuntimeVoiceState)
    supervisor = Supervisor()

    graph.add_node("supervisor", supervisor.invoke)
    graph.add_node("booking_agent", booking_agent)
    graph.add_node("support_agent", support_agent)
    graph.add_node("billing_agent", billing_agent)
    graph.add_node("general_agent", general_agent)

    graph.set_entry_point("supervisor")
    graph.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "booking_agent": "booking_agent",
            "support_agent": "support_agent",
            "billing_agent": "billing_agent",
            "general_agent": "general_agent",
        },
    )
    graph.add_edge("booking_agent", END)
    graph.add_edge("support_agent", END)
    graph.add_edge("billing_agent", END)
    graph.add_edge("general_agent", END)
    return PublicVoiceGraph(graph.compile(checkpointer=checkpointer))


def handle_turn(user_text: str, turn_id: int, cache: SemanticCache, cp: InMemoryCheckpointer) -> dict:
    cached = cache.get(user_text)
    if cached:
        state = {"user_text": user_text, "current_response": cached, "interrupted": False, "turn_id": turn_id}
        cp.save(turn_id, state)
        return state

    response = speculative_response("Agent", f"help with: {user_text}")
    state = {"user_text": user_text, "current_response": response, "interrupted": False, "turn_id": turn_id}
    cache.set(user_text, response)
    cp.save(turn_id, state)
    return state


def _append_agent_response(state: RuntimeVoiceState, response: str) -> RuntimeVoiceState:
    history: list[TurnMessage] = [
        *state["turn_history"],
        {"role": "user", "content": state["current_utterance"]},
        {"role": "assistant", "content": response},
    ]
    return {
        **state,
        "agent_response": response,
        "turn_history": history,
    }


@dataclass
class PublicVoiceGraph:
    compiled_graph: object

    def invoke(self, state: VoiceState) -> VoiceState:
        runtime_state = voice_state_to_runtime(state)
        cfg = {
            "configurable": {
                "thread_id": "voice-thread",
                "checkpoint_ns": "ep4-supervisor",
                "checkpoint_id": state["checkpoint_id"],
            }
        }
        result = self.compiled_graph.invoke(runtime_state, cfg)
        return runtime_to_voice_state(result)


def voice_state_to_runtime(state: VoiceState) -> RuntimeVoiceState:
    runtime: RuntimeVoiceState = {
        "current_utterance": state["current_utterance"],
        "turn_history": state["turn_history"],
        "active_task": state["active_task"],
        "checkpoint_ref": state["checkpoint_id"],
        "in_flight_tts": state["in_flight_tts"],
    }
    if "intent" in state:
        runtime["intent"] = state["intent"]
    if "agent_response" in state:
        runtime["agent_response"] = state["agent_response"]
    if "interrupted" in state:
        runtime["interrupted"] = state["interrupted"]
    return runtime


def runtime_to_voice_state(state: RuntimeVoiceState) -> VoiceState:
    voice_state: VoiceState = {
        "current_utterance": state["current_utterance"],
        "turn_history": state["turn_history"],
        "active_task": state["active_task"],
        "checkpoint_id": state["checkpoint_ref"],
        "in_flight_tts": state["in_flight_tts"],
    }
    if "intent" in state:
        voice_state["intent"] = state["intent"]
    if "agent_response" in state:
        voice_state["agent_response"] = state["agent_response"]
    if "interrupted" in state:
        voice_state["interrupted"] = state["interrupted"]
    return voice_state


if __name__ == "__main__":
    demo_state: VoiceState = {
        "current_utterance": "Can you book a demo for tomorrow?",
        "turn_history": [],
        "active_task": None,
        "checkpoint_id": "turn-1",
        "in_flight_tts": [],
    }
    print(build_graph().invoke(demo_state))
