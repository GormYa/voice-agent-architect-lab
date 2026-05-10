from __future__ import annotations

import asyncio

from pipeline.parallel_gen import generate_group
from pipeline.session_manager import SessionManager
from pipeline.vision import classify_entity


async def run_demo(caption: str) -> dict:
    entity = classify_entity(caption)
    personas = await generate_group([
        (entity.label, entity.era, entity.mood),
        ("narrator", "modern", "friendly"),
    ])
    mgr = SessionManager()
    active = mgr.set_voice(entity.label, personas[entity.label])
    return {"entity": entity.__dict__, "active_voice": active, "voice": mgr.get_active()}


if __name__ == "__main__":
    print(asyncio.run(run_demo("marble statue in a museum hall")))
