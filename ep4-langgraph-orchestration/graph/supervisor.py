from __future__ import annotations

from graph.semantic_cache import SemanticCache
from graph.speculative import speculative_response
from state.redis_checkpointer import InMemoryCheckpointer


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


if __name__ == "__main__":
    cache = SemanticCache()
    cp = InMemoryCheckpointer(store={})
    print(handle_turn("book a demo", 1, cache, cp))
